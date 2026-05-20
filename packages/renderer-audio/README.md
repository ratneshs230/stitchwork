# @stitchwork/renderer-audio

Audiobook sub-pipeline:

1. **SSML 1.1 emission** — AST → SSML, lifting `audio-pronounce` roles to `<phoneme alphabet="ipa">…</phoneme>` or `<sub alias="…">…</sub>` and dropping `ai-provenance` / print-only directives. PLS lexicons supported via `--lexicon path/to/lex.pls`.
2. **ElevenLabs Projects API** — uploads SSML, requests synthesis with `eleven_multilingual_v2` for narration and `eleven_v3` for character voices (hybrid). Polls until done, downloads MP3.
3. **Whisper round-trip QA** — runs Whisper large-v3 on the produced audio, computes WER vs the input plain text (SSML tags stripped). Fails the build if WER > 5%.

## Env vars

- `ELEVENLABS_API_KEY` — required for synthesis.
- `STITCHWORK_VOICE_NARRATION` — voice ID for narration (default: a documentary-style preset).
- `STITCHWORK_VOICE_QUOTE` — voice ID for `practitioner-quote` blocks (defaults to a contrasting voice).

When the key is absent the worker still emits SSML and the project manifest; the synthesis step is skipped with a clear note.

## CLI

```bash
uv run python -m stitchwork_renderer_audio.cli \
  --ast path/to/book.ast.json \
  --out dist/audio \
  --voice-narration <id> \
  --voice-quote <id>
```
