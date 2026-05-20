"""Playwright headless-browser screenshot worker with PII mask overlays."""

from __future__ import annotations
import shutil
from pathlib import Path
from typing import Any

from ..cache import ContentHashCache


def render_screenshot(spec: dict[str, Any], out_path: Path, cache: ContentHashCache | None = None) -> dict[str, Any]:
    """Capture a screenshot of a URL or local HTML, with masked rectangles.

    spec = {
      "url": "https://...",
      "selector": "main"|None,
      "viewport": {"width": 1280, "height": 800},
      "wait_for": "networkidle"|"load",
      "mask": [{"x": 0, "y": 0, "width": 100, "height": 30, "label": "redacted email"}, ...],
      "format": "png",
    }
    """
    fmt = spec.get("format", "png")
    if cache is not None:
        entry = cache.entry("playwright", spec, fmt)
        if cache.exists(entry):
            cache.fetch(entry, out_path)
            return {"ok": True, "cached": True, "path": str(out_path), "key": entry.key}

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"ok": False, "reason": "playwright not installed"}

    url = spec.get("url")
    if not url:
        return {"ok": False, "reason": "spec.url is required"}

    viewport = spec.get("viewport") or {"width": 1280, "height": 800}
    wait_for = spec.get("wait_for", "networkidle")
    mask_specs = spec.get("mask", []) or []
    selector = spec.get("selector")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        page.goto(url, wait_until=wait_for)
        if selector:
            element = page.locator(selector)
            element.screenshot(path=str(out_path))
        else:
            page.screenshot(path=str(out_path), full_page=True)
        browser.close()

    # Overlay masks via Pillow (if installed)
    if mask_specs:
        try:
            from PIL import Image, ImageDraw, ImageFont  # type: ignore
            img = Image.open(out_path).convert("RGBA")
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            for m in mask_specs:
                draw.rectangle(
                    [(m["x"], m["y"]), (m["x"] + m["width"], m["y"] + m["height"])],
                    fill=(0, 0, 0, 255),
                )
                label = m.get("label")
                if label:
                    draw.text((m["x"] + 4, m["y"] + 4), label, fill=(255, 255, 255, 255))
            combined = Image.alpha_composite(img, overlay).convert("RGB")
            combined.save(out_path)
        except ImportError:
            pass

    key = None
    if cache is not None:
        shutil.copyfile(out_path, entry.artifact_path)
        cache.commit(entry, "playwright", spec)
        key = entry.key
    return {"ok": True, "cached": False, "path": str(out_path), "key": key}
