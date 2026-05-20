# @stitchwork/renderer-visual

Three visual workers + a content-hash cache:

| Worker | Tool | Output |
|---|---|---|
| `mermaid` | Mermaid CLI (`mmdc`) | SVG / PNG |
| `matplotlib` | Python matplotlib | PDF / PNG (print: `pdf.fonttype=42`) |
| `playwright` | Playwright (Chromium, headless) | PNG screenshots with PII mask overlays |

## Cache

Cache key = SHA-256 of `(worker_name, spec_canonical_json)`. Cache root: `.stitchwork-cache/visual/` next to the book. A regen is forced when:

- The spec hash changes, or
- The output file is missing, or
- `--no-cache` is passed.

A one-line edit to a chapter body must not invalidate any figure.

## Specs

A "spec" is the inputs a worker needs, normalised to JSON:

```json
{ "worker": "mermaid", "src": "graph TD\nA --> B", "theme": "default", "format": "svg" }
{ "worker": "matplotlib", "kind": "bar", "data": [...], "title": "...", "format": "pdf" }
{ "worker": "playwright", "url": "https://...", "selector": "#main", "mask": [...] }
```

## CLI

```bash
uv run python -m stitchwork_renderer_visual.cli render \
  --spec figure.json --out fig.svg

# Cache stats
uv run python -m stitchwork_renderer_visual.cli stats --book path/to/book
```
