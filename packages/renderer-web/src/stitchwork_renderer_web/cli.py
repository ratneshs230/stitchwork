"""Python shim that defers to the Node preview server.

The actual server is TypeScript (Node 20+ + chokidar + ws). This shim exists so
that the CLI can call `uv run python -m stitchwork_renderer_web.cli` uniformly
with the other worker packages.
"""

from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path

import click


@click.command()
@click.option("--book", "book_path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--port", default=7777, type=int)
def main(book_path: Path, port: int) -> None:
    here = Path(__file__).resolve()
    # ../../../../ from packages/renderer-web/src/stitchwork_renderer_web/cli.py → repo root
    repo_root = here.parents[4]
    web_pkg = repo_root / "packages" / "renderer-web"
    dist_bin = web_pkg / "dist" / "bin.js"
    if not dist_bin.exists():
        click.echo(f"web preview not built; run `pnpm --filter @stitchwork/renderer-web build` (missing {dist_bin})", err=True)
        sys.exit(2)
    proc = subprocess.run(
        ["node", str(dist_bin), "--book", str(book_path), "--port", str(port)],
        env=os.environ.copy(),
    )
    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
