# @stitchwork/lockfile

Content-hash graph for Stitchwork: tracks the dependency relationships between source documents, generated artefacts (figures, screenshots, SSML, audio), and rendered outputs so a one-line edit to chapter 3 does not invalidate the 400 figures in chapter 2.

## File format

`stitchwork.lock` is JSON Lines (one record per line). Each record has:

```json
{
  "kind": "source"|"figure"|"render"|"audio"|"epub"|"pdf",
  "id": "stable identifier",
  "hash": "sha-256 of canonical content",
  "deps": ["id-of-parent-record", ...],
  "meta": {...}
}
```

## Invariants

- A record is invalidated only if its `hash` differs from current OR any of its `deps` is invalidated.
- Sources hash on the raw bytes; renders hash on `(source-hash, locale, edition, renderer-version)`.

## CLI

```bash
uv run python -m stitchwork_lockfile.cli init --book path/to/book
uv run python -m stitchwork_lockfile.cli check --book path/to/book   # exits 0 if up-to-date, 7 if stale
uv run python -m stitchwork_lockfile.cli diff  --book path/to/book   # shows what would regenerate
```
