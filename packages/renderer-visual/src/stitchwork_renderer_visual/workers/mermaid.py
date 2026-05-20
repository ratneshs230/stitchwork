"""Mermaid CLI worker."""

from __future__ import annotations
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from ..cache import ContentHashCache


def render_mermaid(spec: dict[str, Any], out_path: Path, cache: ContentHashCache | None = None) -> dict[str, Any]:
    """Render a Mermaid spec to SVG or PNG.

    spec = {"src": "graph TD\nA-->B", "format": "svg"|"png", "theme": "default"|"dark"}
    """
    fmt = spec.get("format", "svg")
    if cache is not None:
        entry = cache.entry("mermaid", spec, fmt)
        if cache.exists(entry):
            cache.fetch(entry, out_path)
            return {"ok": True, "cached": True, "path": str(out_path), "key": entry.key}

    mmdc = shutil.which("mmdc")
    if mmdc is None:
        return {"ok": False, "reason": "mermaid-cli (mmdc) not installed"}

    src = spec.get("src", "")
    theme = spec.get("theme", "default")
    with tempfile.TemporaryDirectory() as td:
        in_path = Path(td) / "diagram.mmd"
        in_path.write_text(src, encoding="utf-8")
        tmp_out = Path(td) / f"out.{fmt}"
        proc = subprocess.run(
            [mmdc, "-i", str(in_path), "-o", str(tmp_out), "-t", theme, "-b", "transparent"],
            check=False, capture_output=True, text=True,
        )
        if proc.returncode != 0 or not tmp_out.exists():
            return {"ok": False, "reason": proc.stderr.strip() or proc.stdout.strip() or "mmdc failed"}
        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(tmp_out, out_path)

    cached = False
    key = None
    if cache is not None:
        shutil.copyfile(out_path, entry.artifact_path)
        cache.commit(entry, "mermaid", spec)
        key = entry.key
    return {"ok": True, "cached": cached, "path": str(out_path), "key": key}
