# @stitchwork/renderer-typst

Renders Stitchwork AST → Typst source → PDF.

## Behaviour

1. Read AST manifest emitted by the CLI (`<bookid>.ast.json`).
2. Apply locale + edition filtering (locale-variant, edition directives).
3. Walk the AST, emitting Typst markup using the imprint template (`templates/<imprint>.typ`).
4. If the `typst` binary is available, compile to PDF. If not, emit the `.typ` and exit with a non-fatal note — the file is still usable from any Typst install.
5. Optionally post-process the PDF through Ghostscript to PDF/X-1a (`--pdfx` flag; requires `gs` on PATH).

## Templates

| imprint | trim | use |
|---|---|---|
| `legal-press` | 6×9 | Trade non-fiction, legal/professional |
| `kitchen-table` | 5.5×8.5 | Trade non-fiction, smaller hand-feel |
| `workbook` | 8.5×11 | Workbook / journal layouts |

Templates live in `templates/<imprint>.typ`. Add new imprints by adding a template.

## CLI

```bash
uv run python -m stitchwork_renderer_typst.cli \
  --ast path/to/book.ast.json \
  --out dist/pdf
```

Flags:

- `--locale CODE` — locale to resolve for `locale-variant` directives.
- `--edition VER` — edition to gate `edition` directives.
- `--imprint NAME` — override `book.yml` imprint.
- `--pdfx` — post-process to PDF/X-1a via Ghostscript.
- `--keep-typ` — keep intermediate `.typ` source next to the PDF.
