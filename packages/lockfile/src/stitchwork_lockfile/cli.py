"""Lockfile CLI."""

from __future__ import annotations
import json
import sys
from pathlib import Path

import click

from .graph import LockGraph, LockRecord, sha256_file


def _scan_book(book_path: Path) -> dict[str, str]:
    """Hash all chapter sources under book_path/chapters."""
    out: dict[str, str] = {}
    ch_dir = book_path / "chapters"
    if not ch_dir.exists():
        return out
    for f in sorted(ch_dir.glob("*.md")):
        out[f"source:{f.name}"] = sha256_file(f)
    return out


@click.group()
def main() -> None:
    pass


@main.command()
@click.option("--book", required=True, type=click.Path(exists=True, file_okay=False, path_type=Path))
def init(book: Path) -> None:
    g = LockGraph()
    for rid, h in _scan_book(book).items():
        g.add(LockRecord(kind="source", id=rid, hash=h))
    g.save(book / "stitchwork.lock")
    click.echo(f"wrote {book / 'stitchwork.lock'} with {len(g.records)} records")


@main.command()
@click.option("--book", required=True, type=click.Path(exists=True, file_okay=False, path_type=Path))
def check(book: Path) -> None:
    g = LockGraph.load(book / "stitchwork.lock")
    current = _scan_book(book)
    stale = g.stale(current)
    if not stale:
        click.echo("up-to-date")
        sys.exit(0)
    click.echo(f"{len(stale)} stale record(s):")
    for s in stale:
        click.echo(f"  - {s}")
    sys.exit(7)


@main.command()
@click.option("--book", required=True, type=click.Path(exists=True, file_okay=False, path_type=Path))
def diff(book: Path) -> None:
    g = LockGraph.load(book / "stitchwork.lock")
    current = _scan_book(book)
    stale = g.stale(current)
    click.echo(json.dumps({"stale": stale, "total": len(g.records)}, indent=2))


if __name__ == "__main__":
    main()
