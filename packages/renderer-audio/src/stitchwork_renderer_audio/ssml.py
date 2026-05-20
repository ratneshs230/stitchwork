"""AST → SSML 1.1 emission."""

from __future__ import annotations
from html import escape
from typing import Any


SUPPRESS_DIRECTIVES = {"ai-provenance", "visual-ref", "workbook-prompt"}


def _inline_to_ssml(node: dict[str, Any]) -> str:
    t = node.get("type")
    if t == "text":
        return escape(node.get("value", ""))
    if t == "strong":
        # SSML <emphasis level="strong"> is widely supported
        inner = "".join(_inline_to_ssml(c) for c in node.get("children", []))
        return f'<emphasis level="strong">{inner}</emphasis>'
    if t == "emphasis":
        inner = "".join(_inline_to_ssml(c) for c in node.get("children", []))
        return f'<emphasis level="moderate">{inner}</emphasis>'
    if t == "inlineCode":
        # Spell out code as-is, slower
        return f'<prosody rate="0.9">{escape(node.get("value", ""))}</prosody>'
    if t == "role":
        name = node.get("name")
        text = node.get("text") or ""
        opts = node.get("options", {})
        if name == "audio-pronounce":
            ipa = opts.get("ipa")
            alias = opts.get("alias")
            ssml = opts.get("ssml")
            if ipa:
                return f'<phoneme alphabet="ipa" ph="{escape(ipa)}">{escape(text)}</phoneme>'
            if alias:
                return f'<sub alias="{escape(alias)}">{escape(text)}</sub>'
            if ssml:
                # Caller-provided raw SSML fragment for the role text
                return ssml
        if name == "regulatory-cite":
            # The text only; the citation URL/statute is for print/EPUB
            return escape(text)
    return ""


def _block_to_ssml(node: dict[str, Any], voice_narration: str | None, voice_quote: str | None) -> str:
    t = node.get("type")
    if t == "heading":
        depth = node.get("depth", 1)
        inner = "".join(_inline_to_ssml(c) for c in node.get("children", []))
        # Insert a longer break for chapter / section openings
        break_ms = 1200 if depth == 1 else 600
        return f'<break time="{break_ms}ms"/><prosody rate="0.95"><emphasis level="strong">{inner}</emphasis></prosody><break time="500ms"/>'
    if t == "paragraph":
        inner = "".join(_inline_to_ssml(c) for c in node.get("children", []))
        return f"<p>{inner}</p>"
    if t == "blockquote":
        children = "".join(_block_to_ssml(c, voice_narration, voice_quote) for c in node.get("children", []))
        return f"<p>{children}</p>"
    if t == "code":
        # Skip code blocks from narration — they are unreadable as audio
        return ""
    if t == "thematicBreak":
        return '<break time="1500ms"/>'
    if t == "list":
        items = "".join(
            "<p>" + "".join(_block_to_ssml(c, voice_narration, voice_quote) for c in li.get("children", [])) + "</p>"
            for li in node.get("children", [])
        )
        return items
    if t == "directive":
        return _directive_to_ssml(node, voice_narration, voice_quote)
    return ""


def _directive_to_ssml(node: dict[str, Any], voice_narration: str | None, voice_quote: str | None) -> str:
    name = node.get("name")
    if name in SUPPRESS_DIRECTIVES:
        return ""
    children = "".join(_block_to_ssml(c, voice_narration, voice_quote) for c in node.get("children", []))
    if name == "practitioner-quote":
        # Voice switch via <voice> element
        voice = voice_quote or "default-quote"
        return f'<break time="600ms"/><voice name="{escape(voice)}">{children}</voice><break time="600ms"/>'
    if name in ("locale-variant", "edition"):
        return children
    return children


def ast_to_ssml(
    ast: dict[str, Any],
    title: str,
    voice_narration: str | None = None,
    voice_quote: str | None = None,
    lang: str = "en-IN",
) -> str:
    body = "".join(_block_to_ssml(c, voice_narration, voice_quote) for c in ast.get("children", []))
    narration_voice = voice_narration or "default-narration"
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<speak version="1.1" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{lang}">\n'
        f'  <metadata>\n    <title>{escape(title)}</title>\n  </metadata>\n'
        f'  <voice name="{escape(narration_voice)}">\n'
        f"    {body}\n"
        f"  </voice>\n"
        f"</speak>\n"
    )
