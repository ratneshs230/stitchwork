"""Visual worker CLI: render and inspect."""

from __future__ import annotations
import json
from pathlib import Path

import click

from .cache import ContentHashCache
from .workers.mermaid import render_mermaid
from .workers.matplotlib_chart import render_matplotlib
from .workers.playwright_shot import render_screenshot


@click.group()
def main() -> None:
    pass


@main.command()
@click.option("--spec", "spec_path", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--out", "out_path", required=True, type=click.Path(dir_okay=False, path_type=Path))
@click.option("--cache-root", default=".stitchwork-cache", type=click.Path(file_okay=False, path_type=Path))
@click.option("--no-cache", is_flag=True)
def render(spec_path: Path, out_path: Path, cache_root: Path, no_cache: bool) -> None:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    cache = None if no_cache else ContentHashCache(cache_root)
    worker = spec.get("worker")
    if worker == "mermaid":
        res = render_mermaid(spec, out_path, cache)
    elif worker == "matplotlib":
        res = render_matplotlib(spec, out_path, cache)
    elif worker == "playwright":
        res = render_screenshot(spec, out_path, cache)
    else:
        click.echo(json.dumps({"ok": False, "reason": f"unknown worker {worker}"}), err=True)
        raise click.exceptions.Exit(2)
    click.echo(json.dumps(res, indent=2))
    if not res.get("ok"):
        raise click.exceptions.Exit(1)


@main.command()
@click.option("--cache-root", default=".stitchwork-cache", type=click.Path(file_okay=False, path_type=Path))
def stats(cache_root: Path) -> None:
    cache = ContentHashCache(cache_root)
    click.echo(json.dumps(cache.stats(), indent=2))


if __name__ == "__main__":
    main()
