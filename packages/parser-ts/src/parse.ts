import type {
  BlockNode,
  DirectiveNode,
  HeadingNode,
  InlineNode,
  ParagraphNode,
  RoleNode,
  RootNode,
  TextNode,
} from './types.js';
import { ErrorCodes, StitchworkParseError } from './errors.js';
import { validateOptions } from './validate.js';
import { isKnownDirective, getDirective } from '@stitchwork/shared-schemas';

const DIRECTIVE_FENCE_RE = /^:::\{([a-z][a-z0-9-]*)\}(?:\s+(.*))?$/;
const DIRECTIVE_END_RE = /^:::\s*$/;
const OPTION_RE = /^:([a-z][a-z0-9_]*):\s*(.*)$/;
const FRONTMATTER_FENCE = '---';
const HEADING_RE = /^(#{1,6})\s+(.+)$/;
const CODE_FENCE_RE = /^```(\w+)?\s*$/;
const ROLE_RE = /\{([a-z][a-z0-9-]*)\}`([^`]*)`(?:\[([^\]]*)\])?/g;

export interface ParseResult {
  ast: RootNode;
  warnings: string[];
}

interface Line {
  text: string;
  no: number; // 1-indexed
}

function tokenize(src: string): Line[] {
  return src.split(/\r?\n/).map((text, i) => ({ text, no: i + 1 }));
}

function parseFrontmatter(lines: Line[]): { fm: Record<string, unknown>; rest: Line[] } {
  if (lines.length === 0 || lines[0].text.trim() !== FRONTMATTER_FENCE) {
    return { fm: {}, rest: lines };
  }
  const end = lines.findIndex((l, i) => i > 0 && l.text.trim() === FRONTMATTER_FENCE);
  if (end === -1) {
    throw new StitchworkParseError(
      'unterminated frontmatter',
      ErrorCodes.MALFORMED_FRONTMATTER,
      1
    );
  }
  const fm: Record<string, unknown> = {};
  for (let i = 1; i < end; i++) {
    const line = lines[i].text;
    const m = /^([a-zA-Z][a-zA-Z0-9_-]*):\s*(.*)$/.exec(line);
    if (m) {
      let value: unknown = m[2];
      if (value === 'true') value = true;
      else if (value === 'false') value = false;
      else if (typeof value === 'string' && /^-?\d+$/.test(value)) value = Number(value);
      fm[m[1]] = value;
    }
  }
  return { fm, rest: lines.slice(end + 1) };
}

function parseInline(text: string, line: number): InlineNode[] {
  const nodes: InlineNode[] = [];
  let last = 0;
  ROLE_RE.lastIndex = 0;
  let m: RegExpExecArray | null;
  while ((m = ROLE_RE.exec(text)) !== null) {
    if (m.index > last) {
      nodes.push(...parseEmphAndStrong(text.slice(last, m.index)));
    }
    const name = m[1];
    const optionsRaw = m[2];
    const displayText = m[3];
    if (!isKnownDirective(name) || getDirective(name)?.kind !== 'role') {
      throw new StitchworkParseError(
        `unknown role "${name}"`,
        ErrorCodes.UNKNOWN_ROLE,
        line
      );
    }
    const rawOptions: Record<string, string> = {};
    for (const part of optionsRaw.split(',').map((p) => p.trim()).filter(Boolean)) {
      const eq = part.indexOf('=');
      if (eq === -1) {
        throw new StitchworkParseError(
          `malformed role option "${part}" (expected key=value)`,
          ErrorCodes.INVALID_OPTION_VALUE,
          line
        );
      }
      rawOptions[part.slice(0, eq).trim()] = part.slice(eq + 1).trim();
    }
    const options = validateOptions({
      directiveName: name,
      rawOptions,
      hasBody: false,
      line,
    });
    const role: RoleNode = { type: 'role', name, options };
    if (displayText !== undefined) role.text = displayText;
    nodes.push(role);
    last = m.index + m[0].length;
  }
  if (last < text.length) {
    nodes.push(...parseEmphAndStrong(text.slice(last)));
  }
  return nodes;
}

function parseEmphAndStrong(text: string): InlineNode[] {
  // Minimal: split on **...** and *...*; everything else is text.
  const out: InlineNode[] = [];
  let i = 0;
  let buf = '';
  const flush = () => {
    if (buf.length > 0) {
      const tn: TextNode = { type: 'text', value: buf };
      out.push(tn);
      buf = '';
    }
  };
  while (i < text.length) {
    if (text.startsWith('**', i)) {
      const end = text.indexOf('**', i + 2);
      if (end !== -1) {
        flush();
        out.push({
          type: 'strong',
          children: [{ type: 'text', value: text.slice(i + 2, end) }],
        });
        i = end + 2;
        continue;
      }
    }
    if (text[i] === '*') {
      const end = text.indexOf('*', i + 1);
      if (end !== -1) {
        flush();
        out.push({
          type: 'emphasis',
          children: [{ type: 'text', value: text.slice(i + 1, end) }],
        });
        i = end + 1;
        continue;
      }
    }
    if (text[i] === '`') {
      const end = text.indexOf('`', i + 1);
      if (end !== -1) {
        flush();
        out.push({ type: 'inlineCode', value: text.slice(i + 1, end) });
        i = end + 1;
        continue;
      }
    }
    buf += text[i];
    i++;
  }
  flush();
  return out;
}

function slugify(s: string): string {
  return s
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

interface BlockParseState {
  lines: Line[];
  i: number;
}

function parseBlocks(state: BlockParseState, endMarker?: RegExp): BlockNode[] {
  const out: BlockNode[] = [];
  while (state.i < state.lines.length) {
    const line = state.lines[state.i];
    const text = line.text;

    if (endMarker && endMarker.test(text)) {
      return out;
    }

    if (text.trim() === '') {
      state.i++;
      continue;
    }

    const fence = DIRECTIVE_FENCE_RE.exec(text);
    if (fence) {
      out.push(parseDirective(state));
      continue;
    }

    const heading = HEADING_RE.exec(text);
    if (heading) {
      const depth = heading[1].length as 1 | 2 | 3 | 4 | 5 | 6;
      const content = heading[2];
      const node: HeadingNode = {
        type: 'heading',
        depth,
        children: parseInline(content, line.no),
        id: slugify(content),
      };
      out.push(node);
      state.i++;
      continue;
    }

    const codeFence = CODE_FENCE_RE.exec(text);
    if (codeFence) {
      const lang = codeFence[1];
      state.i++;
      const start = state.i;
      while (state.i < state.lines.length && !/^```\s*$/.test(state.lines[state.i].text)) {
        state.i++;
      }
      const body = state.lines
        .slice(start, state.i)
        .map((l) => l.text)
        .join('\n');
      state.i++; // closing fence
      out.push({ type: 'code', lang, value: body });
      continue;
    }

    // accumulate paragraph until blank line / new block
    const startLine = line.no;
    const buf: string[] = [];
    while (state.i < state.lines.length) {
      const t = state.lines[state.i].text;
      if (
        t.trim() === '' ||
        DIRECTIVE_FENCE_RE.test(t) ||
        HEADING_RE.test(t) ||
        CODE_FENCE_RE.test(t) ||
        (endMarker && endMarker.test(t))
      ) {
        break;
      }
      buf.push(t);
      state.i++;
    }
    const para: ParagraphNode = {
      type: 'paragraph',
      children: parseInline(buf.join(' '), startLine),
    };
    out.push(para);
  }
  return out;
}

function parseDirective(state: BlockParseState): DirectiveNode {
  const line = state.lines[state.i];
  const fence = DIRECTIVE_FENCE_RE.exec(line.text)!;
  const name = fence[1];
  const args = fence[2];
  if (!isKnownDirective(name)) {
    throw new StitchworkParseError(
      `unknown directive "${name}"`,
      ErrorCodes.UNKNOWN_DIRECTIVE,
      line.no
    );
  }
  const spec = getDirective(name)!;
  state.i++;
  const rawOptions: Record<string, string> = {};
  // options block: contiguous `:key: value` lines at the top
  while (state.i < state.lines.length) {
    const opt = OPTION_RE.exec(state.lines[state.i].text);
    if (!opt) break;
    rawOptions[opt[1]] = opt[2];
    state.i++;
  }

  // optionally consume single blank line separating options from body
  let bodyLines: Line[] = [];
  let hasBody = false;
  if (spec.kind === 'block' && spec.hasBody !== false) {
    while (state.i < state.lines.length && !DIRECTIVE_END_RE.test(state.lines[state.i].text)) {
      bodyLines.push(state.lines[state.i]);
      state.i++;
    }
    if (state.i >= state.lines.length) {
      throw new StitchworkParseError(
        `unclosed directive "${name}" (started at line ${line.no})`,
        ErrorCodes.UNCLOSED_DIRECTIVE,
        line.no
      );
    }
    // trim leading/trailing blank lines from body
    while (bodyLines.length > 0 && bodyLines[0].text.trim() === '') bodyLines.shift();
    while (bodyLines.length > 0 && bodyLines[bodyLines.length - 1].text.trim() === '') {
      bodyLines.pop();
    }
    hasBody = bodyLines.length > 0;
    state.i++; // consume closing :::
  } else {
    // no-body directive — still expect :::
    while (state.i < state.lines.length && !DIRECTIVE_END_RE.test(state.lines[state.i].text)) {
      // tolerate blank lines between options and closing fence
      if (state.lines[state.i].text.trim() !== '') {
        throw new StitchworkParseError(
          `directive "${name}" does not accept a body, got "${state.lines[state.i].text}"`,
          ErrorCodes.BODY_NOT_ALLOWED,
          state.lines[state.i].no
        );
      }
      state.i++;
    }
    if (state.i >= state.lines.length) {
      throw new StitchworkParseError(
        `unclosed directive "${name}" (started at line ${line.no})`,
        ErrorCodes.UNCLOSED_DIRECTIVE,
        line.no
      );
    }
    state.i++; // consume closing :::
  }

  const options = validateOptions({
    directiveName: name,
    rawOptions,
    hasBody,
    line: line.no,
  });

  const children: BlockNode[] = bodyLines.length
    ? parseBlocks({ lines: bodyLines, i: 0 })
    : [];

  const node: DirectiveNode = {
    type: 'directive',
    name,
    options,
    children,
  };
  if (args) node.args = args.trim();
  return node;
}

export function parse(src: string): ParseResult {
  const lines = tokenize(src);
  const { fm, rest } = parseFrontmatter(lines);
  const children = parseBlocks({ lines: rest, i: 0 });
  const ast: RootNode = { type: 'root', children };
  if (Object.keys(fm).length > 0) ast.frontmatter = fm;
  return { ast, warnings: [] };
}
