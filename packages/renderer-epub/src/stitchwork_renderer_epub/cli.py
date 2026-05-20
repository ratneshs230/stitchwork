"""CLI entry for the EPUB renderer worker."""

from __future__ import annotations
import json
import sys
from pathlib import Path

import click

from .render import render_epub


@click.command()
@click.option("--ast", "ast_path", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--out", "out_dir", required=True, type=click.Path(file_okay=False, path_type=Path))
@click.option("--locale", default=None)
@click.option("--edition", default=None)
def main(ast_path: Path, out_dir: Path, locale: str | None, edition: str | None) -> None:
    res = render_epub(ast_path=ast_path, out_dir=out_dir, locale=locale, edition=edition)
    click.echo(json.dumps({
        "ok": res.ok,
        "epub": str(res.epub_path) if res.epub_path else None,
        "xhtml_dir": str(res.xhtml_dir),
        "notes": res.notes,
        "validation": res.validation,
    }, indent=2))
    sys.exit(0 if res.ok else 1)


if __name__ == "__main__":
    main()
