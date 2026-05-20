import { describe, expect, it } from 'vitest';
import { parse } from '../src/parse.js';
import { ErrorCodes, StitchworkParseError } from '../src/errors.js';

describe('parser — frontmatter + headings + paragraphs', () => {
  it('parses frontmatter then heading then paragraph', () => {
    const src = `---
title: Test
draft: false
chapter: 3
---

# Hello world

A paragraph with **bold** and *italic*.`;
    const { ast } = parse(src);
    expect(ast.frontmatter).toEqual({ title: 'Test', draft: false, chapter: 3 });
    expect(ast.children.length).toBe(2);
    expect(ast.children[0]).toMatchObject({ type: 'heading', depth: 1, id: 'hello-world' });
    expect(ast.children[1]).toMatchObject({ type: 'paragraph' });
  });
});

describe('directive: ai-provenance', () => {
  it('accepts a valid block with no body', () => {
    const src = `:::{ai-provenance}
:model: claude-opus-4-7
:prompt_hash: 7f3a91c
:generated_at: 2026-05-17T09:14:00Z
:human_edits: heavy
:editor: priya.k
:::`;
    const { ast } = parse(src);
    expect(ast.children[0]).toMatchObject({
      type: 'directive',
      name: 'ai-provenance',
      options: {
        model: 'claude-opus-4-7',
        prompt_hash: '7f3a91c',
        human_edits: 'heavy',
        editor: 'priya.k',
      },
      children: [],
    });
  });

  it('rejects missing required option', () => {
    const src = `:::{ai-provenance}
:model: claude-opus-4-7
:generated_at: 2026-05-17T09:14:00Z
:human_edits: heavy
:::`;
    expect(() => parse(src)).toThrowError(/SW003.*prompt_hash/);
  });

  it('rejects unknown option (no silent drop)', () => {
    const src = `:::{ai-provenance}
:model: claude-opus-4-7
:prompt_hash: 7f3a91c
:generated_at: 2026-05-17T09:14:00Z
:human_edits: heavy
:rogue_option: nope
:::`;
    expect(() => parse(src)).toThrowError(/SW002.*rogue_option/);
  });

  it('rejects invalid enum value for human_edits', () => {
    const src = `:::{ai-provenance}
:model: claude-opus-4-7
:prompt_hash: 7f3a91c
:generated_at: 2026-05-17T09:14:00Z
:human_edits: medium
:::`;
    expect(() => parse(src)).toThrowError(/SW004.*human_edits/);
  });

  it('rejects body on a no-body directive', () => {
    const src = `:::{ai-provenance}
:model: claude-opus-4-7
:prompt_hash: 7f3a91c
:generated_at: 2026-05-17T09:14:00Z
:human_edits: heavy

Some prose that should not be here.
:::`;
    expect(() => parse(src)).toThrowError(/SW006/);
  });
});

describe('directive: practitioner-quote', () => {
  it('parses a quote block with body', () => {
    const src = `:::{practitioner-quote}
:source_name: Dr. Meera Iyer
:role: Senior Agronomist, ICAR
:jurisdiction: IN
:consent_id: pq-2026-0431
:rev_share_bps: 50

"Most beginner gardeners over-lime. Test before you amend."
:::`;
    const { ast } = parse(src);
    expect(ast.children[0]).toMatchObject({
      type: 'directive',
      name: 'practitioner-quote',
      options: { jurisdiction: 'IN', rev_share_bps: 50 },
    });
    const d = ast.children[0] as { children: { type: string }[] };
    expect(d.children.length).toBe(1);
  });

  it('rejects rev_share_bps out of range', () => {
    const src = `:::{practitioner-quote}
:source_name: X
:role: Y
:jurisdiction: IN
:consent_id: q1
:rev_share_bps: 99999

Body.
:::`;
    expect(() => parse(src)).toThrowError(/SW004.*rev_share_bps/);
  });
});

describe('directive: locale-variant', () => {
  it('accepts array of locales', () => {
    const src = `:::{locale-variant}
:locales: [IN, US-CA]

Body.
:::`;
    const { ast } = parse(src);
    expect((ast.children[0] as { options: { locales: string[] } }).options.locales).toEqual([
      'IN',
      'US-CA',
    ]);
  });

  it('rejects malformed locale code', () => {
    const src = `:::{locale-variant}
:locales: [india, US]

Body.
:::`;
    expect(() => parse(src)).toThrowError(/SW004/);
  });
});

describe('directive: edition', () => {
  it('accepts since-only', () => {
    const src = `:::{edition}
:since: 2027.1

New for 2027.
:::`;
    const { ast } = parse(src);
    expect((ast.children[0] as { options: { since: string } }).options.since).toBe('2027.1');
  });

  it('rejects when none of since/until/range present', () => {
    const src = `:::{edition}

Body.
:::`;
    expect(() => parse(src)).toThrowError(/SW007/);
  });
});

describe('directive: workbook-prompt', () => {
  it('accepts fill kind with lines', () => {
    const src = `:::{workbook-prompt}
:id: ch3-baseline
:kind: fill
:lines: 4

Write something.
:::`;
    const { ast } = parse(src);
    expect((ast.children[0] as { options: { lines: number } }).options.lines).toBe(4);
  });

  it('rejects lines > 40', () => {
    const src = `:::{workbook-prompt}
:id: x
:kind: fill
:lines: 99

Body.
:::`;
    expect(() => parse(src)).toThrowError(/SW004.*lines/);
  });
});

describe('directive: visual-ref', () => {
  it('accepts prompt-only (no src)', () => {
    const src = `:::{visual-ref}
:role: diagram
:id: fig-3-1
:alt: pH scale band labels
:prompt: Horizontal pH ruler with bands.
:::`;
    const { ast } = parse(src);
    expect((ast.children[0] as { options: { role: string } }).options.role).toBe('diagram');
  });

  it('rejects when neither prompt nor src given', () => {
    const src = `:::{visual-ref}
:role: diagram
:id: f1
:alt: needs at least four chars
:::`;
    expect(() => parse(src)).toThrowError(/SW007/);
  });
});

describe('roles: regulatory-cite and audio-pronounce', () => {
  it('parses regulatory-cite inline role', () => {
    const src = `The {regulatory-cite}\`jurisdiction=IN, current_as_of=2026-05, source_url=https://example.com/x, statute=Soil-Card\`[free soil card] is widely used.`;
    const { ast } = parse(src);
    const para = ast.children[0] as { children: { type: string; name?: string; text?: string }[] };
    const role = para.children.find((c) => c.type === 'role');
    expect(role).toMatchObject({ name: 'regulatory-cite', text: 'free soil card' });
  });

  it('parses audio-pronounce inline role with ipa', () => {
    const src = `When you say {audio-pronounce}\`ipa=/ˈnaɪ.trə.dʒən/\`[nitrogen] aloud.`;
    const { ast } = parse(src);
    const para = ast.children[0] as { children: { type: string; name?: string }[] };
    const role = para.children.find((c) => c.type === 'role');
    expect(role).toMatchObject({ name: 'audio-pronounce' });
  });

  it('audio-pronounce rejects two hint kinds at once', () => {
    const src = `Say {audio-pronounce}\`ipa=/ɛks/, alias=ex\`[X] please.`;
    expect(() => parse(src)).toThrowError(/SW007/);
  });
});

describe('unknown directive / role', () => {
  it('throws SW001 for unknown directive', () => {
    const src = `:::{bogus-directive}
:foo: bar
:::`;
    expect(() => parse(src)).toThrowError(/SW001/);
  });

  it('throws SW008 for unknown inline role', () => {
    const src = `An inline {bogus-role}\`x=1\`[oops] is bad.`;
    expect(() => parse(src)).toThrowError(/SW008/);
  });
});

describe('error code stability', () => {
  it('exports the documented codes', () => {
    expect(ErrorCodes.UNKNOWN_DIRECTIVE).toBe('SW001');
    expect(ErrorCodes.UNKNOWN_OPTION).toBe('SW002');
    expect(ErrorCodes.MISSING_REQUIRED_OPTION).toBe('SW003');
    expect(ErrorCodes.INVALID_OPTION_VALUE).toBe('SW004');
    expect(ErrorCodes.UNCLOSED_DIRECTIVE).toBe('SW005');
    expect(ErrorCodes.BODY_NOT_ALLOWED).toBe('SW006');
    expect(ErrorCodes.CONSTRAINT_VIOLATION).toBe('SW007');
    expect(ErrorCodes.UNKNOWN_ROLE).toBe('SW008');
  });

  it('parser errors carry code + line', () => {
    try {
      parse(`:::{bogus}\n:::`);
      throw new Error('should have thrown');
    } catch (e) {
      expect(e).toBeInstanceOf(StitchworkParseError);
      expect((e as StitchworkParseError).code).toBe('SW001');
      expect((e as StitchworkParseError).line).toBe(1);
    }
  });
});
