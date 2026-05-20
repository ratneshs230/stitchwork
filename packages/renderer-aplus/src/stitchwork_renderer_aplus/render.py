"""A+ content HTML module renderer."""

from __future__ import annotations
import json
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any


MODULE_HEADER_IMAGE_TEXT = "STANDARD_HEADER_IMAGE_TEXT"
MODULE_TEXT_BLOCK = "STANDARD_TEXT_BLOCK"
MODULE_QUOTE = "STANDARD_QUOTE"
MODULE_IMAGE_TEXT_OVERLAY = "STANDARD_IMAGE_TEXT_OVERLAY"
MODULE_COMPARISON_TABLE = "STANDARD_COMPARISON_TABLE"


@dataclass
class AplusResult:
    out_dir: Path
    modules: list[dict[str, Any]]


def _first_paragraph_text(ast: dict[str, Any]) -> str:
    for node in ast.get("children", []):
        if node.get("type") == "paragraph":
            parts: list[str] = []
            for inline in node.get("children", []):
                if inline.get("type") == "text":
                    parts.append(inline.get("value", ""))
            return " ".join(parts).strip()
    return ""


def _first_directive(ast: dict[str, Any], name: str) -> dict[str, Any] | None:
    stack = list(ast.get("children", []))
    while stack:
        n = stack.pop(0)
        if isinstance(n, dict) and n.get("type") == "directive" and n.get("name") == name:
            return n
        if isinstance(n, dict) and n.get("children"):
            stack.extend(n["children"])
    return None


def _truncate_words(s: str, n: int) -> str:
    parts = s.split()
    if len(parts) <= n:
        return s
    return " ".join(parts[:n]) + "…"


def render_aplus(manifest: dict[str, Any], out_dir: Path) -> AplusResult:
    out_dir.mkdir(parents=True, exist_ok=True)
    book = manifest["manifest"]
    title = book.get("title", "")
    subtitle = book.get("subtitle", "")
    authors = ", ".join(book.get("authors", []) or [])

    modules: list[dict[str, Any]] = []

    # 1. Header module
    header_html = (
        f'<section class="sw-aplus-header"><h1>{escape(title)}</h1>'
        f'<p class="sw-aplus-subtitle">{escape(subtitle)}</p>'
        f'<p class="sw-aplus-byline">by {escape(authors)}</p></section>'
    )
    modules.append({"module": MODULE_HEADER_IMAGE_TEXT, "file": "01-header.html", "html": header_html})

    # 2. Opening-chapter text block
    first_chapter = manifest.get("chapters", [{}])[0]
    body_text = _first_paragraph_text(first_chapter.get("ast", {}))
    body_text = _truncate_words(body_text, 80) or escape(subtitle)
    text_html = f'<section class="sw-aplus-text"><p>{escape(body_text)}</p></section>'
    modules.append({"module": MODULE_TEXT_BLOCK, "file": "02-text.html", "html": text_html})

    # 3. First practitioner-quote (if any)
    quote = _first_directive(first_chapter.get("ast", {}), "practitioner-quote")
    if quote:
        opts = quote.get("options", {})
        body = _first_paragraph_text(quote)
        quote_html = (
            f'<section class="sw-aplus-quote"><blockquote>{escape(body)}</blockquote>'
            f'<footer>— {escape(opts.get("source_name", ""))}, '
            f'<span>{escape(opts.get("role", ""))}</span></footer></section>'
        )
        modules.append({"module": MODULE_QUOTE, "file": "03-quote.html", "html": quote_html})

    # 4. First infographic visual-ref
    visual = _first_directive(first_chapter.get("ast", {}), "visual-ref")
    if visual:
        opts = visual.get("options", {})
        if str(opts.get("role")) in ("infographic", "hero", "diagram"):
            v_html = (
                f'<section class="sw-aplus-visual">'
                f'<figure><div class="sw-aplus-placeholder">[ {escape(opts.get("id", ""))} ]</div>'
                f'<figcaption>{escape(opts.get("alt", ""))}</figcaption></figure>'
                f'</section>'
            )
            modules.append({"module": MODULE_IMAGE_TEXT_OVERLAY, "file": "04-visual.html", "html": v_html})

    # 5. Comparison table — author-supplied via book.yml `comparison`
    comparison = book.get("comparison") if isinstance(book.get("comparison"), list) else None
    if comparison:
        rows = "".join(
            f"<tr><td>{escape(str(r.get('feature', '')))}</td>"
            f"<td>{escape(str(r.get('this_book', '')))}</td>"
            f"<td>{escape(str(r.get('alternative', '')))}</td></tr>"
            for r in comparison
        )
        table_html = (
            f'<section class="sw-aplus-table"><table>'
            f'<thead><tr><th>Feature</th><th>This book</th><th>Alternatives</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></section>'
        )
        modules.append({"module": MODULE_COMPARISON_TABLE, "file": "05-table.html", "html": table_html})

    for m in modules:
        (out_dir / m["file"]).write_text(m["html"], encoding="utf-8")
    index = {"book": book["id"], "title": title, "modules": [{"module": m["module"], "file": m["file"]} for m in modules]}
    (out_dir / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")

    return AplusResult(out_dir=out_dir, modules=modules)
