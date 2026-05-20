"""AST → Typst source → PDF renderer."""

from __future__ import annotations
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .filters import apply_filters

TEMPLATES_DIR = Path(__file__).parent / "templates"


@dataclass
class RenderResult:
    typst_path: Path
    pdf_path: Path | None
    pdfx_path: Path | None
    ok: bool
    notes: list[str]


def _escape(text: str) -> str:
    """Escape Typst special characters in body text."""
    # See https://typst.app/docs/reference/syntax/ — minimal escape set
    return (
        text
        .replace("\\", "\\\\")
        .replace("#", "\\#")
        .replace("$", "\\$")
        .replace("@", "\\@")
        .replace("*", "\\*")
        .replace("_", "\\_")
        .replace("`", "\\`")
    )


def _render_inline(node: dict[str, Any]) -> str:
    t = node.get("type")
    if t == "text":
        return _escape(node.get("value", ""))
    if t == "strong":
        inner = "".join(_render_inline(c) for c in node.get("children", []))
        return f"*{inner}*"
    if t == "emphasis":
        inner = "".join(_render_inline(c) for c in node.get("children", []))
        return f"_{inner}_"
    if t == "inlineCode":
        return f"`{node.get('value', '')}`"
    if t == "role":
        name = node.get("name")
        text = node.get("text") or ""
        opts = node.get("options", {})
        if name == "regulatory-cite":
            # Render display text and footnote with the source URL + statute
            url = opts.get("source_url", "")
            statute = opts.get("statute", "")
            return f"{_escape(text)}#footnote[{_escape(statute)}. #link(\"{url}\")[{url}]]"
        if name == "audio-pronounce":
            # Print: just render the text; SSML hint is for audio path
            return _escape(text)
    # Fallback
    return ""


def _render_block(node: dict[str, Any]) -> str:
    t = node.get("type")
    if t == "heading":
        depth = node.get("depth", 1)
        prefix = "=" * depth
        inline = "".join(_render_inline(c) for c in node.get("children", []))
        return f"{prefix} {inline}\n\n"
    if t == "paragraph":
        inline = "".join(_render_inline(c) for c in node.get("children", []))
        return f"{inline}\n\n"
    if t == "code":
        lang = node.get("lang") or ""
        body = node.get("value", "")
        return f"```{lang}\n{body}\n```\n\n"
    if t == "directive":
        return _render_directive(node)
    if t == "thematicBreak":
        return "#line(length: 100%, stroke: 0.5pt + luma(180))\n\n"
    if t == "blockquote":
        children = "".join(_render_block(c) for c in node.get("children", []))
        return f"#quote(block: true)[{children}]\n\n"
    if t == "list":
        items = ""
        for child in node.get("children", []):
            inner = "".join(_render_block(c) for c in child.get("children", []))
            marker = "+" if node.get("ordered") else "-"
            items += f"{marker} {inner.strip()}\n"
        return items + "\n"
    return ""


def _render_directive(node: dict[str, Any]) -> str:
    name = node.get("name")
    opts = node.get("options", {})
    children_md = "".join(_render_block(c) for c in node.get("children", []))
    if name == "ai-provenance":
        # Suppress in print per design spec — leave a Typst comment for traceability
        return f"// ai-provenance suppressed: model={opts.get('model')} edits={opts.get('human_edits')}\n\n"
    if name == "practitioner-quote":
        src = opts.get("source_name", "")
        role = opts.get("role", "")
        return (
            "#block(fill: luma(245), inset: 12pt, radius: 4pt, breakable: false)[\n"
            f"{children_md}\n"
            f"#align(right)[#text(size: 9pt, fill: luma(80))[— {_escape(src)}, {_escape(role)}]]"
            "]\n\n"
        )
    if name == "locale-variant":
        # Already filtered upstream; render as plain content
        return children_md
    if name == "edition":
        return children_md
    if name == "workbook-prompt":
        lines = int(opts.get("lines", 4) or 4)
        rules = "\n".join(["#line(length: 100%, stroke: 0.6pt + luma(150))" for _ in range(lines)])
        return (
            "#block(stroke: 0.5pt + luma(180), inset: 10pt, radius: 4pt, breakable: false)[\n"
            f"#text(weight: \"semibold\")[Workbook prompt — {_escape(opts.get('id', ''))}]\n\n"
            f"{children_md}\n"
            f"#v(6pt)\n{rules}\n"
            "]\n\n"
        )
    if name == "visual-ref":
        alt = opts.get("alt", "")
        id_ = opts.get("id", "")
        return (
            "#figure(\n"
            "  block(stroke: 0.5pt + luma(180), inset: 24pt, radius: 4pt)[\n"
            f"    #align(center)[#text(size: 9pt, fill: luma(100))[FIGURE PLACEHOLDER — {_escape(id_)}]]"
            "  ],\n"
            f"  caption: [{_escape(alt)}]\n"
            f") <fig-{_escape(id_)}>\n\n"
        )
    return children_md


def _load_template(imprint: str) -> str:
    candidate = TEMPLATES_DIR / f"{imprint}.typ"
    if not candidate.exists():
        candidate = TEMPLATES_DIR / "legal-press.typ"
    return candidate.read_text(encoding="utf-8")


def _emit_typst_source(manifest: dict[str, Any], filtered_chapters: list[dict[str, Any]]) -> str:
    book = manifest["manifest"]
    imprint = book.get("imprint", "legal-press")
    template = _load_template(imprint)
    body_chunks: list[str] = []
    for ch in filtered_chapters:
        ast = ch["ast"]
        body_chunks.append(f"// === chapter: {ch['id']} ===\n")
        for child in ast.get("children", []):
            body_chunks.append(_render_block(child))
    body = "".join(body_chunks)
    return (
        template
        .replace("{{TITLE}}", book.get("title", ""))
        .replace("{{SUBTITLE}}", book.get("subtitle", ""))
        .replace("{{AUTHORS}}", ", ".join(book.get("authors", []) or []))
        .replace("{{BODY}}", body)
    )


def _compile_pdf(typ_path: Path, pdf_path: Path) -> tuple[bool, str]:
    typst_bin = shutil.which("typst")
    if typst_bin is None:
        return False, "typst binary not found on PATH; emitted .typ only"
    try:
        proc = subprocess.run(
            [typst_bin, "compile", str(typ_path), str(pdf_path)],
            check=False,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            return False, f"typst compile failed: {proc.stderr.strip() or proc.stdout.strip()}"
        return True, ""
    except OSError as e:
        return False, f"typst compile error: {e}"


def _gs_to_pdfx(pdf_in: Path, pdf_out: Path) -> tuple[bool, str]:
    gs_bin = shutil.which("gs") or shutil.which("gswin64c") or shutil.which("gswin32c")
    if gs_bin is None:
        return False, "ghostscript not found on PATH; skipping PDF/X-1a"
    proc = subprocess.run(
        [
            gs_bin,
            "-dPDFX",
            "-dBATCH",
            "-dNOPAUSE",
            "-dNOOUTERSAVE",
            "-sDEVICE=pdfwrite",
            "-sColorConversionStrategy=CMYK",
            "-dProcessColorModel=/DeviceCMYK",
            f"-sOutputFile={pdf_out}",
            str(pdf_in),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return False, f"ghostscript failed: {proc.stderr.strip() or proc.stdout.strip()}"
    return True, ""


def render_book(
    ast_path: Path,
    out_dir: Path,
    *,
    locale: str | None = None,
    edition: str | None = None,
    imprint: str | None = None,
    pdfx: bool = False,
    keep_typ: bool = True,
) -> RenderResult:
    manifest = json.loads(ast_path.read_text(encoding="utf-8"))
    if imprint:
        manifest["manifest"]["imprint"] = imprint
    locale = locale or manifest.get("locale")
    edition = edition or manifest.get("edition")
    notes: list[str] = []

    filtered_chapters: list[dict[str, Any]] = []
    for ch in manifest.get("chapters", []):
        ast = ch["ast"]
        ast = dict(ast)
        ast["children"] = apply_filters(ast.get("children", []), locale, edition)
        filtered_chapters.append({"id": ch["id"], "ast": ast})

    typst_src = _emit_typst_source(manifest, filtered_chapters)
    out_dir.mkdir(parents=True, exist_ok=True)
    book_id = manifest["manifest"]["id"]
    typ_path = out_dir / f"{book_id}.typ"
    typ_path.write_text(typst_src, encoding="utf-8")

    pdf_path = out_dir / f"{book_id}.pdf"
    ok, msg = _compile_pdf(typ_path, pdf_path)
    if not ok:
        notes.append(msg)
        pdf_path = None  # type: ignore[assignment]

    pdfx_path: Path | None = None
    if pdfx and pdf_path is not None:
        candidate = out_dir / f"{book_id}-x1a.pdf"
        ok2, msg2 = _gs_to_pdfx(pdf_path, candidate)
        if ok2:
            pdfx_path = candidate
        else:
            notes.append(msg2)

    if not keep_typ:
        try:
            typ_path.unlink()
        except OSError:
            pass

    return RenderResult(
        typst_path=typ_path,
        pdf_path=pdf_path,
        pdfx_path=pdfx_path,
        ok=(pdf_path is not None) or (os.environ.get("STITCHWORK_ALLOW_TYP_ONLY") == "1"),
        notes=notes,
    )
