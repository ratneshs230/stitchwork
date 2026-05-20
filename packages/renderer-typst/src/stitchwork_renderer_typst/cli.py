"""CLI entry for the Typst renderer worker."""

from __future__ import annotations
import json
import sys
from pathlib import Path

import click

from .render import render_book


@click.command()
@click.option("--ast", "ast_path", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--out", "out_dir", required=True, type=click.Path(file_okay=False, path_type=Path))
@click.option("--locale", default=None, help="Locale to resolve locale-variant directives (e.g. en-IN)")
@click.option("--edition", default=None, help="Edition gate (e.g. 2026.1)")
@click.option("--imprint", default=None, help="Override book.yml imprint template")
@click.option("--pdfx", is_flag=True, help="Post-process to PDF/X-1a via Ghostscript")
@click.option("--keep-typ/--no-keep-typ", default=True)
def main(ast_path: Path, out_dir: Path, locale: str | None, edition: str | None, imprint: str | None, pdfx: bool, keep_typ: bool) -> None:
    result = render_book(
        ast_path=ast_path,
        out_dir=out_dir,
        locale=locale,
        edition=edition,
        imprint=imprint,
        pdfx=pdfx,
        keep_typ=keep_typ,
    )
    payload = {
        "ok": result.ok,
        "typst": str(result.typst_path),
        "pdf": str(result.pdf_path) if result.pdf_path else None,
        "pdfx": str(result.pdfx_path) if result.pdfx_path else None,
        "notes": result.notes,
    }
    click.echo(json.dumps(payload, indent=2))
    sys.exit(0 if result.ok else 1)


if __name__ == "__main__":
    main()
