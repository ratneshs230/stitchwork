# Contributing to Stitchwork

## Development setup

```bash
# Node/TypeScript (parser + VSCode extension)
corepack enable
pnpm install

# Python (CLI + renderers)
uv sync

# Run tests
pnpm test              # TypeScript
uv run pytest          # Python
```

## Commit convention

`<type>(<scope>): <description>`

Types: `feat`, `fix`, `docs`, `test`, `chore`, `refactor`

Scopes: `parser`, `cli`, `typst`, `epub`, `ssml`, `preview`, `vscode`

## PR checklist

- [ ] All directive schemas validated (no silent-drop)
- [ ] Unit tests for new directive options
- [ ] `pnpm test` passes
- [ ] `uv run pytest` passes
- [ ] `stitchwork validate` passes on sample book
