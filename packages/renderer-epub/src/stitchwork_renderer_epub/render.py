"""AST → EPUB 3.3 with EPUB Accessibility 1.1 metadata."""

from __future__ import annotations
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:  # Optional — installable as extra
    from ebooklib import epub  # type: ignore
    HAVE_EBOOKLIB = True
except ImportError:  # pragma: no cover
    epub = None  # type: ignore
    HAVE_EBOOKLIB = False

from .xhtml import STYLESHEET, chapter_to_xhtml


@dataclass
class EpubRenderResult:
    epub_path: Path | None
    xhtml_dir: Path
    ok: bool
    notes: list[str]
    validation: dict[str, Any]


def _apply_filters(ast: dict[str, Any], locale: str | None, edition: str | None) -> dict[str, Any]:
    # Import here to avoid forcing the typst worker on the path for EPUB-only runs
    try:
        from stitchwork_renderer_typst.filters import apply_filters  # type: ignore
    except ImportError:
        # Fall back to no-op if the typst package isn't installed alongside
        return ast
    new = dict(ast)
    new["children"] = apply_filters(ast.get("children", []), locale, edition)
    return new


def _epubcheck(path: Path) -> dict[str, Any]:
    jar = os.environ.get("EPUBCHECK_JAR")
    if not jar:
        return {"ran": False, "reason": "EPUBCHECK_JAR not set"}
    java = shutil.which("java")
    if not java:
        return {"ran": False, "reason": "java not on PATH"}
    proc = subprocess.run(
        [java, "-jar", jar, "--json", "-", str(path)],
        check=False, capture_output=True, text=True,
    )
    return {
        "ran": True,
        "exit": proc.returncode,
        "stdout_head": proc.stdout[:1000],
        "stderr_head": proc.stderr[:500],
    }


def _ace(path: Path, report_dir: Path) -> dict[str, Any]:
    ace = shutil.which("ace") or shutil.which("ace.cmd")
    if not ace:
        return {"ran": False, "reason": "Ace by DAISY not on PATH"}
    report_dir.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [ace, "-o", str(report_dir), str(path)],
        check=False, capture_output=True, text=True,
    )
    return {
        "ran": True,
        "exit": proc.returncode,
        "stdout_head": proc.stdout[:800],
        "stderr_head": proc.stderr[:500],
    }


def render_epub(ast_path: Path, out_dir: Path, *, locale: str | None = None, edition: str | None = None) -> EpubRenderResult:
    manifest = json.loads(ast_path.read_text(encoding="utf-8"))
    book = manifest["manifest"]
    locale = locale or manifest.get("locale")
    edition = edition or manifest.get("edition")

    out_dir.mkdir(parents=True, exist_ok=True)
    xhtml_dir = out_dir / "xhtml"
    xhtml_dir.mkdir(exist_ok=True)
    notes: list[str] = []

    chapter_html: list[tuple[str, str, str]] = []  # (file_name, title, content)
    for ch in manifest.get("chapters", []):
        ast = _apply_filters(ch["ast"], locale, edition)
        # Extract chapter title from first heading
        title = book.get("title", ch["id"])
        for c in ast.get("children", []):
            if c.get("type") == "heading" and c.get("depth") == 1:
                title = "".join(t.get("value", "") for t in c.get("children", []) if t.get("type") == "text") or title
                break
        html = chapter_to_xhtml(ast, title)
        fname = f"{ch['id']}.xhtml"
        (xhtml_dir / fname).write_text(html, encoding="utf-8")
        chapter_html.append((fname, title, html))

    epub_path: Path | None = None
    if not HAVE_EBOOKLIB:
        notes.append("ebooklib not installed; emitted XHTML only")
        return EpubRenderResult(epub_path=None, xhtml_dir=xhtml_dir, ok=True, notes=notes, validation={})

    eb = epub.EpubBook()
    eb.set_identifier(book.get("isbn", {}).get("ebook") or f"stitchwork-{book['id']}")
    eb.set_title(book.get("title", book["id"]))
    eb.set_language((locale or "en").split("-")[0])
    for author in book.get("authors", []) or []:
        eb.add_author(author)

    # EPUB Accessibility 1.1 metadata
    eb.add_metadata("DC", "rights", "© Stitchwork contributors")
    eb.add_metadata(None, "meta", "textual", {"property": "schema:accessMode"})
    eb.add_metadata(None, "meta", "visual", {"property": "schema:accessMode"})
    eb.add_metadata(None, "meta", "textual", {"property": "schema:accessModeSufficient"})
    eb.add_metadata(None, "meta", "structuralNavigation", {"property": "schema:accessibilityFeature"})
    eb.add_metadata(None, "meta", "alternativeText", {"property": "schema:accessibilityFeature"})
    eb.add_metadata(None, "meta", "tableOfContents", {"property": "schema:accessibilityFeature"})
    eb.add_metadata(None, "meta", "readingOrder", {"property": "schema:accessibilityFeature"})
    eb.add_metadata(None, "meta", "none", {"property": "schema:accessibilityHazard"})
    eb.add_metadata(
        None,
        "meta",
        "This publication conforms to EPUB Accessibility 1.1 and WCAG 2.1 Level AA.",
        {"property": "schema:accessibilitySummary"},
    )

    css = epub.EpubItem(uid="style_main", file_name="css/stitchwork.css", media_type="text/css", content=STYLESHEET)
    eb.add_item(css)

    spine_items: list[Any] = ["nav"]
    toc: list[Any] = []
    for fname, title, html in chapter_html:
        item = epub.EpubHtml(title=title, file_name=f"xhtml/{fname}", lang=(locale or "en").split("-")[0])
        item.content = html
        item.add_item(css)
        eb.add_item(item)
        spine_items.append(item)
        toc.append(item)

    eb.toc = tuple(toc)
    eb.add_item(epub.EpubNcx())
    eb.add_item(epub.EpubNav())
    eb.spine = spine_items

    epub_path = out_dir / f"{book['id']}.epub"
    epub.write_epub(str(epub_path), eb, {})

    validation = {
        "epubcheck": _epubcheck(epub_path),
        "ace": _ace(epub_path, out_dir / "ace-report"),
    }
    return EpubRenderResult(epub_path=epub_path, xhtml_dir=xhtml_dir, ok=True, notes=notes, validation=validation)
