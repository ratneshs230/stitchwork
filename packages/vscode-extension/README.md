# Stitchwork VSCode Extension

Authoring surface for Stitchwork MyST documents.

## Features

- Syntax highlighting for the 8 Stitchwork directives (`ai-provenance`, `practitioner-quote`, etc.) and 2 inline roles.
- Live validation via the parser — directive option errors surface as squiggles with code (SW001-SW009).
- Outline command (`Stitchwork: Reveal Outline`) — quick-pick over headings + directive sites.
- Preview command (`Stitchwork: Open Live Preview`) — launches the localhost preview server.
- Validate command (`Stitchwork: Validate Current Book`) — runs the CLI in a terminal.

## Settings

- `stitchwork.cliPath` (default: `stitchwork`) — path to the CLI binary.
- `stitchwork.previewPort` (default: `7777`).

## Install (dev)

```bash
pnpm --filter @stitchwork/vscode-extension build
# then F5 from the package folder in VSCode to launch an Extension Development Host
```
