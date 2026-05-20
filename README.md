# Stitchwork

Open-source publishing toolchain. One MyST Markdown source → print-ready PDF, EPUB 3.3, audiobook SSML, web HTML, and Amazon A+ content modules.

## Architecture

```
MyST source (.md) → mystmd parser + Stitchwork directives → JSON AST
                                                               │
                    ┌──────────────────────────────────────────┤
                    │                 │              │          │
                 Typst PDF       EPUB 3.3         SSML      HTML/A+
              (KDP/Ingram)   (Kindle/Kobo)   (ElevenLabs)  (web)
```

## Stack

- **Source**: MyST Markdown + 8 custom directives
- **Parser**: TypeScript (`packages/parser`) — extends `mystmd`
- **CLI**: Python (`src/stitchwork/`) — Click-based
- **Print**: Typst 0.14+ → Ghostscript → PDF/X-1a
- **EPUB**: pandoc Lua filters + ebooklib → EPUB 3.3
- **Audio**: SSML 1.1 → ElevenLabs Projects API + Whisper QA
- **CI**: GitHub Actions (Linux + macOS + Windows)

## Quick start

```bash
# Install
pip install stitchwork   # or: uv add stitchwork

# Build a book
stitchwork build books/my-book --locale en-IN --output-dir dist/

# Validate
stitchwork validate books/my-book

# Preview (localhost:7777)
stitchwork preview books/my-book

# Publish
stitchwork publish books/my-book --target kdp
```

## Custom directives

| Directive | Kind | Purpose |
|---|---|---|
| `ai-provenance` | block | Per-section AI generation tracking (EU AI Act Art. 50) |
| `practitioner-quote` | block | Real-practitioner attribution with rev-share metadata |
| `regulatory-cite` | inline role | Jurisdictional citation, swappable by locale |
| `locale-variant` | block | Conditional content by country/locale |
| `edition` | block | Version-range gating (`since`, `until`) |
| `workbook-prompt` | block | Fillable journal/workbook elements |
| `visual-ref` | block | Figure placeholder with semantic role + AI gen prompt |
| `audio-pronounce` | inline role | SSML pronunciation hint (IPA or alias) |

## Validation gates (CI-enforced)

- `mystmd validate` — directive schema validation
- `epubcheck --failonwarnings` — EPUB structural conformance
- `ace` — EPUB accessibility (WCAG 2.1 AA)
- `gs -dPDFX` — PDF/X-1a validation
- Whisper round-trip WER ≤ 5% per chapter

## License

Apache 2.0. See [LICENSE](LICENSE).
