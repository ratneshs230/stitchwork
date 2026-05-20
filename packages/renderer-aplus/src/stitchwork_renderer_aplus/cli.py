"""A+ content CLI."""

from __future__ import annotations
import json
import sys
from pathlib import Path

import click

from .render import render_aplus


@click.command()
@click.option("--ast", "ast_path", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--out", "out_dir", required=True, type=click.Path(file_okay=False, path_type=Path))
@click.option("--locale", default=None)
@click.option("--edition", default=None)
def main(ast_path: Path, out_dir: Path, locale: str | None, edition: str | None) -> None:
    manifest = json.loads(ast_path.read_text(encoding="utf-8"))
    res = render_aplus(manifest, out_dir)
    click.echo(json.dumps({
        "ok": True,
        "module_count": len(res.modules),
        "out": str(res.out_dir),
        "modules": [m["module"] for m in res.modules],
    }, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
