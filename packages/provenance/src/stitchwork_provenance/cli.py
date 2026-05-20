"""Provenance CLI."""

from __future__ import annotations
import json
import sys
from pathlib import Path

import click

from .jsonld import emit_ledger


@click.group()
def main() -> None:
    pass


@main.command()
@click.option("--ast", "ast_path", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--out", "out_dir", required=True, type=click.Path(file_okay=False, path_type=Path))
def emit(ast_path: Path, out_dir: Path) -> None:
    manifest = json.loads(ast_path.read_text(encoding="utf-8"))
    p = emit_ledger(manifest, out_dir)
    click.echo(json.dumps({"ledger": str(p)}, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
