"""matplotlib chart worker — print-grade output."""

from __future__ import annotations
import shutil
from pathlib import Path
from typing import Any

from ..cache import ContentHashCache


def render_matplotlib(spec: dict[str, Any], out_path: Path, cache: ContentHashCache | None = None) -> dict[str, Any]:
    """Render a small matplotlib chart spec.

    spec = {"kind": "bar"|"line"|"scatter", "data": {"x": [...], "y": [...]},
             "title": "...", "xlabel": "...", "ylabel": "...", "format": "pdf"|"png"}

    Honours ``pdf.fonttype = 42`` so embedded fonts are PDF/X friendly.
    """
    fmt = spec.get("format", "pdf")
    if cache is not None:
        entry = cache.entry("matplotlib", spec, fmt)
        if cache.exists(entry):
            cache.fetch(entry, out_path)
            return {"ok": True, "cached": True, "path": str(out_path), "key": entry.key}

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return {"ok": False, "reason": "matplotlib not installed"}

    matplotlib.rcParams["pdf.fonttype"] = 42  # TrueType, embeddable
    matplotlib.rcParams["ps.fonttype"] = 42

    fig, ax = plt.subplots(figsize=(6, 3.5))
    kind = spec.get("kind", "bar")
    data = spec.get("data", {})
    x = data.get("x", [])
    y = data.get("y", [])

    if kind == "bar":
        ax.bar(x, y)
    elif kind == "line":
        ax.plot(x, y)
    elif kind == "scatter":
        ax.scatter(x, y)
    else:
        return {"ok": False, "reason": f"unsupported chart kind: {kind}"}

    if spec.get("title"):
        ax.set_title(spec["title"])
    if spec.get("xlabel"):
        ax.set_xlabel(spec["xlabel"])
    if spec.get("ylabel"):
        ax.set_ylabel(spec["ylabel"])
    ax.grid(True, linestyle=":", alpha=0.4)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, format=fmt, dpi=300, bbox_inches="tight")
    plt.close(fig)

    key = None
    if cache is not None:
        shutil.copyfile(out_path, entry.artifact_path)
        cache.commit(entry, "matplotlib", spec)
        key = entry.key
    return {"ok": True, "cached": False, "path": str(out_path), "key": key}
