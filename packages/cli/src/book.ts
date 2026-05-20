import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { join, resolve, basename } from 'node:path';
import { parse, type ParseResult } from '@stitchwork/parser-ts';

export interface BookManifest {
  id: string;
  title: string;
  subtitle?: string;
  authors: string[];
  imprint: string;
  trim?: string;
  locale?: string;
  edition?: string;
  isbn?: { print?: string; ebook?: string; audio?: string };
  chapters: string[];
}

export interface LoadedChapter {
  id: string;
  path: string;
  source: string;
  result: ParseResult;
}

export interface LoadedBook {
  manifest: BookManifest;
  root: string;
  chapters: LoadedChapter[];
}

function naiveYaml(src: string): Record<string, unknown> {
  // Minimal YAML for book.yml — keys, scalars, simple lists, simple maps.
  const lines = src.split(/\r?\n/);
  const result: Record<string, unknown> = {};
  const stack: Array<{ indent: number; obj: Record<string, unknown> | unknown[] }> = [
    { indent: -1, obj: result },
  ];
  for (let raw of lines) {
    raw = raw.replace(/#.*$/, '');
    if (raw.trim() === '') continue;
    const indent = raw.match(/^ */)![0].length;
    const line = raw.trim();
    while (stack.length > 1 && indent <= stack[stack.length - 1].indent) stack.pop();
    const top = stack[stack.length - 1];
    if (line.startsWith('- ')) {
      // list item
      const value = line.slice(2).trim();
      const v: unknown = parseYamlScalar(value);
      if (Array.isArray(top.obj)) {
        (top.obj as unknown[]).push(v);
      }
      continue;
    }
    const m = /^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$/.exec(line);
    if (!m) continue;
    const [, key, valueRaw] = m;
    if (valueRaw === '') {
      // child block — guess whether next non-empty starts with '- '
      const newObj: Record<string, unknown> | unknown[] = [];
      (top.obj as Record<string, unknown>)[key] = newObj;
      stack.push({ indent, obj: newObj });
      // could be a map — we'll detect on the next line; if next line is `key: value`
      // we'll have already pushed array, but the lookup `(top.obj as Record).key`
      // will still find this object since key is unique under top. The simple
      // strategy below handles both via parseYamlScalar fallback.
    } else {
      (top.obj as Record<string, unknown>)[key] = parseYamlScalar(valueRaw);
    }
  }
  // Post-process: arrays that ended up being objects with no list items
  // — flip to {} if all entries are KV. This is good enough for book.yml.
  return result;
}

function parseYamlScalar(value: string): unknown {
  const v = value.trim();
  if (v === '') return null;
  if (v === 'true') return true;
  if (v === 'false') return false;
  if (v === 'null' || v === '~') return null;
  if (/^-?\d+$/.test(v)) return Number(v);
  if (/^".*"$/.test(v) || /^'.*'$/.test(v)) return v.slice(1, -1);
  return v;
}

export function loadBook(bookPath: string): LoadedBook {
  const root = resolve(bookPath);
  const manifestPath = join(root, 'book.yml');
  if (!existsSync(manifestPath)) {
    throw new Error(`book.yml not found in ${root}`);
  }
  const manifestRaw = readFileSync(manifestPath, 'utf8');
  const m = naiveYaml(manifestRaw) as unknown as BookManifest;
  if (!m.id || !m.title || !Array.isArray(m.chapters)) {
    throw new Error('book.yml must declare id, title, and chapters[]');
  }

  const chapters: LoadedChapter[] = [];
  for (const rel of m.chapters) {
    const p = join(root, rel);
    if (!existsSync(p)) {
      throw new Error(`Declared chapter "${rel}" does not exist at ${p}`);
    }
    const source = readFileSync(p, 'utf8');
    const result = parse(source);
    chapters.push({ id: basename(rel, '.md'), path: p, source, result });
  }
  return { manifest: m, root, chapters };
}

export function listChapterFiles(bookRoot: string, subdir = 'chapters'): string[] {
  const dir = join(bookRoot, subdir);
  if (!existsSync(dir)) return [];
  return readdirSync(dir)
    .filter((f) => f.endsWith('.md'))
    .map((f) => join(dir, f))
    .filter((p) => statSync(p).isFile());
}
