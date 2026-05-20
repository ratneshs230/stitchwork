# sample-book / ai-indian-advocate

Canonical Stitchwork test fixture. Used by parser tests, CLI integration tests, and renderer smoke tests in CI.

Built from this source:

```bash
pnpm stitchwork build packages/sample-book/ai-indian-advocate --target pdf
```

Exercises (as of chapter 1):

- `ai-provenance` — chapter-level AI generation metadata
- `regulatory-cite` — inline jurisdictional citation
- `locale-variant` — IN vs US/UK/AU body
- `practitioner-quote` — attributed senior counsel quote with rev-share
- `workbook-prompt` — fillable 6-line journal element
- `visual-ref` — diagram placeholder with AI generation prompt
- `audio-pronounce` — IPA pronunciation hint
