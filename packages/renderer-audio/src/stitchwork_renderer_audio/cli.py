"""Audio worker CLI."""

from __future__ import annotations
import json
import sys
from pathlib import Path

import click

from .render import render_audiobook


@click.command()
@click.option("--ast", "ast_path", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--out", "out_dir", required=True, type=click.Path(file_okay=False, path_type=Path))
@click.option("--locale", default=None)
@click.option("--edition", default=None)
@click.option("--voice-narration", default=None)
@click.option("--voice-quote", default=None)
@click.option("--wer-threshold", default=0.05, type=float)
def main(
    ast_path: Path,
    out_dir: Path,
    locale: str | None,
    edition: str | None,
    voice_narration: str | None,
    voice_quote: str | None,
    wer_threshold: float,
) -> None:
    res = render_audiobook(
        ast_path=ast_path,
        out_dir=out_dir,
        voice_narration=voice_narration,
        voice_quote=voice_quote,
        locale=locale,
        edition=edition,
        wer_threshold=wer_threshold,
    )
    click.echo(json.dumps({
        "ok": res.ok,
        "ssml": [str(p) for p in res.ssml_paths],
        "mp3": [str(p) for p in res.mp3_paths],
        "qa": res.qa,
        "notes": res.notes,
    }, indent=2))
    sys.exit(0 if res.ok else 1)


if __name__ == "__main__":
    main()
