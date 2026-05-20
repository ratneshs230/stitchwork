# @stitchwork/renderer-aplus

Renders Stitchwork AST → **Amazon A+ Content HTML modules** for KDP product listings.

## Modules emitted

| Stitchwork source | A+ module |
|---|---|
| Book title + subtitle + cover thumbnail | `STANDARD_HEADER_IMAGE_TEXT` |
| Opening chapter excerpt (≤ 300 words) | `STANDARD_TEXT_BLOCK` |
| First `practitioner-quote` block | `STANDARD_QUOTE` |
| First `visual-ref` with `role=infographic` | `STANDARD_IMAGE_TEXT_OVERLAY` |
| Comparison table (auto-generated from metadata if present) | `STANDARD_COMPARISON_TABLE` |

Output: a directory with one HTML file per module, plus an `index.json` describing the module sequence (for the KDP A+ uploader).

## CLI

```bash
uv run python -m stitchwork_renderer_aplus.cli \
  --ast path/to/book.ast.json --out dist/aplus
```
