# @stitchwork/renderer-epub

Renders Stitchwork AST → EPUB 3.3 with EPUB Accessibility 1.1 metadata.

## Pipeline

1. Read AST manifest from the CLI.
2. Apply locale/edition filters (shared filter logic).
3. For each chapter, transform AST → XHTML via the per-node renderer. Directives become semantic `<section>`/`<aside>` elements with role attributes; inline roles become `<span>` with class hooks.
4. Pandoc post-process is **optional** — if `pypandoc` is available we route through it for footnote rendering, otherwise we use the built-in XHTML emitter.
5. Build the EPUB container with `ebooklib` — manifest, spine, nav (HTML + NCX for backwards compatibility), accessibility metadata.
6. Emit `.epub` and run EPUBCheck + Ace by DAISY if available; non-fatal warnings are reported, errors fail the build.

## Accessibility (EPUB Accessibility 1.1)

- `<meta>` schema:accessibilityFeature/Hazard/MediaActiveContent/AccessMode/AccessModeSufficient
- `<title>` and `<h1>` on every chapter
- Alt text from `visual-ref.alt` (required by schema, so non-empty)
- ARIA roles for `practitioner-quote` (`role="doc-pullquote"`) and `workbook-prompt` (`role="form"`)

## CLI

```bash
uv run python -m stitchwork_renderer_epub.cli \
  --ast path/to/book.ast.json \
  --out dist/epub
```
