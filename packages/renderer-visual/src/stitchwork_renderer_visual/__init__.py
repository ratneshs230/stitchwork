"""Stitchwork visual sub-pipeline."""

__version__ = "0.1.0"

from .cache import ContentHashCache
from .workers.mermaid import render_mermaid
from .workers.matplotlib_chart import render_matplotlib
from .workers.playwright_shot import render_screenshot

__all__ = [
    "ContentHashCache",
    "render_mermaid",
    "render_matplotlib",
    "render_screenshot",
    "__version__",
]
