# @stitchwork/provenance

Emits the three layers of AI provenance Stitchwork commits to:

1. **C2PA sidecars** (`.c2pa`) — per-image attestations with the source model, prompt hash, edit history. Uses `py-c2pa` when available; otherwise emits a parseable JSON stub with the same fields.
2. **IPTC AI fields** — embedded in image metadata via Pillow `XMP` chunks (XMP-iptcExt Digital Source Type, AI generation indicator).
3. **JSON-LD ledger** — `META-INF/provenance.jsonld` packaged with every EPUB and shipped alongside every PDF: one record per `ai-provenance` directive, linked to the chapter and to any C2PA sidecars for figures generated for that chapter.

Compliance ceiling: **EU AI Act Article 50** (binds 2026-08), **India IT Rules 2026-02** (deepfake disclosure), **NIST AI RMF 600-1**.

## CLI

```bash
uv run python -m stitchwork_provenance.cli emit \
  --ast path/to/book.ast.json \
  --out dist/provenance
```
