"""AST → XHTML emission for Stitchwork EPUB."""

from __future__ import annotations
from html import escape
from typing import Any


def _inline(node: dict[str, Any]) -> str:
    t = node.get("type")
    if t == "text":
        return escape(node.get("value", ""))
    if t == "strong":
        return f"<strong>{''.join(_inline(c) for c in node.get('children', []))}</strong>"
    if t == "emphasis":
        return f"<em>{''.join(_inline(c) for c in node.get('children', []))}</em>"
    if t == "inlineCode":
        return f"<code>{escape(node.get('value', ''))}</code>"
    if t == "role":
        name = node.get("name")
        text = node.get("text") or ""
        opts = node.get("options", {})
        if name == "regulatory-cite":
            url = escape(opts.get("source_url", ""))
            statute = escape(opts.get("statute", ""))
            jur = escape(opts.get("jurisdiction", ""))
            return (
                f'<a class="sw-cite" href="{url}" data-jurisdiction="{jur}" '
                f'data-statute="{statute}">{escape(text)}</a>'
            )
        if name == "audio-pronounce":
            ipa = opts.get("ipa")
            alias = opts.get("alias")
            ssml = opts.get("ssml")
            data = ""
            if ipa:
                data += f' data-ipa="{escape(ipa)}"'
            if alias:
                data += f' data-alias="{escape(alias)}"'
            if ssml:
                data += f' data-ssml="{escape(ssml)}"'
            return f'<span class="sw-pronounce"{data}>{escape(text)}</span>'
    return ""


def _block(node: dict[str, Any]) -> str:
    t = node.get("type")
    if t == "heading":
        depth = node.get("depth", 1)
        inner = "".join(_inline(c) for c in node.get("children", []))
        slug = escape(node.get("id", ""))
        return f'<h{depth} id="{slug}">{inner}</h{depth}>\n'
    if t == "paragraph":
        inner = "".join(_inline(c) for c in node.get("children", []))
        return f"<p>{inner}</p>\n"
    if t == "code":
        lang = escape(node.get("lang") or "")
        return f'<pre><code class="language-{lang}">{escape(node.get("value", ""))}</code></pre>\n'
    if t == "thematicBreak":
        return "<hr />\n"
    if t == "blockquote":
        return f"<blockquote>{''.join(_block(c) for c in node.get('children', []))}</blockquote>\n"
    if t == "list":
        tag = "ol" if node.get("ordered") else "ul"
        items = "".join(
            f"<li>{''.join(_block(c) for c in li.get('children', []))}</li>"
            for li in node.get("children", [])
        )
        return f"<{tag}>{items}</{tag}>\n"
    if t == "directive":
        return _directive(node)
    return ""


def _directive(node: dict[str, Any]) -> str:
    name = node.get("name")
    opts = node.get("options", {})
    children = "".join(_block(c) for c in node.get("children", []))
    if name == "ai-provenance":
        attrs = " ".join(f'data-{k.replace("_", "-")}="{escape(str(v))}"' for k, v in opts.items())
        return f'<meta class="sw-ai-provenance" {attrs} />\n'
    if name == "practitioner-quote":
        src = escape(opts.get("source_name", ""))
        role = escape(opts.get("role", ""))
        jur = escape(opts.get("jurisdiction", ""))
        consent = escape(opts.get("consent_id", ""))
        bps = escape(str(opts.get("rev_share_bps", "")))
        return (
            f'<aside class="sw-practitioner-quote" role="doc-pullquote" '
            f'data-jurisdiction="{jur}" data-consent-id="{consent}" data-rev-share-bps="{bps}">'
            f"{children}"
            f'<footer class="sw-attribution">— {src}, <span class="sw-role">{role}</span></footer>'
            "</aside>\n"
        )
    if name in ("locale-variant", "edition"):
        return f'<section class="sw-{name}">{children}</section>\n'
    if name == "workbook-prompt":
        id_ = escape(opts.get("id", ""))
        kind = escape(opts.get("kind", ""))
        lines = int(opts.get("lines", 0) or 0)
        lines_html = ""
        if lines:
            lines_html = "".join(
                f'<input class="sw-wb-line" type="text" aria-label="line {i+1}" />'
                for i in range(lines)
            )
        return (
            f'<section class="sw-workbook" data-kind="{kind}" id="wb-{id_}" role="form" aria-label="workbook prompt {id_}">'
            f"{children}"
            f'<div class="sw-wb-lines">{lines_html}</div>'
            "</section>\n"
        )
    if name == "visual-ref":
        role = escape(opts.get("role", ""))
        id_ = escape(opts.get("id", ""))
        alt = escape(opts.get("alt", ""))
        src = opts.get("src")
        if src:
            return f'<figure class="sw-visual" data-role="{role}" id="fig-{id_}"><img src="{escape(src)}" alt="{alt}" /><figcaption>{alt}</figcaption></figure>\n'
        return (
            f'<figure class="sw-visual sw-visual-placeholder" data-role="{role}" id="fig-{id_}">'
            f'<div class="sw-placeholder">FIGURE: {alt}</div>'
            f'<figcaption>{alt}</figcaption>'
            "</figure>\n"
        )
    return children


def chapter_to_xhtml(ast: dict[str, Any], chapter_title: str) -> str:
    body = "".join(_block(c) for c in ast.get("children", []))
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en">
<head>
  <meta charset="utf-8" />
  <title>{escape(chapter_title)}</title>
  <link rel="stylesheet" type="text/css" href="../css/stitchwork.css" />
</head>
<body>
<section epub:type="chapter">
{body}
</section>
</body>
</html>
"""


STYLESHEET = """/* Stitchwork EPUB default stylesheet */
body { font-family: serif; line-height: 1.55; margin: 1em; }
h1, h2, h3 { font-family: sans-serif; }
.sw-practitioner-quote {
  border-left: 3px solid #888;
  padding: 0.6em 0.9em;
  background: #f5f5f5;
  margin: 1.2em 0;
}
.sw-attribution { font-size: 0.9em; color: #555; margin-top: 0.4em; }
.sw-cite { text-decoration: underline dotted; }
.sw-workbook {
  border: 1px solid #aaa;
  padding: 1em;
  margin: 1.2em 0;
  border-radius: 4px;
}
.sw-wb-line { display: block; width: 100%; border: 0; border-bottom: 1px solid #999; margin: 6px 0; padding: 4px 0; }
.sw-visual-placeholder .sw-placeholder {
  border: 1px dashed #999;
  padding: 2em;
  text-align: center;
  font-size: 0.9em;
  color: #777;
}
"""
