"""Smoke test for the Typst renderer."""

from __future__ import annotations
import json
from pathlib import Path

from stitchwork_renderer_typst.render import render_book


def _make_manifest(tmp: Path) -> Path:
    payload = {
        "manifest": {
            "id": "smoke",
            "title": "Smoke",
            "subtitle": "Renderer smoke test",
            "authors": ["Test"],
            "imprint": "legal-press",
        },
        "locale": "en-IN",
        "edition": "2026.1",
        "chapters": [
            {
                "id": "ch01",
                "ast": {
                    "type": "root",
                    "children": [
                        {"type": "heading", "depth": 1, "children": [{"type": "text", "value": "Smoke"}]},
                        {"type": "paragraph", "children": [{"type": "text", "value": "Hello."}]},
                        {
                            "type": "directive",
                            "name": "ai-provenance",
                            "options": {"model": "claude-opus-4-7", "human_edits": "light"},
                            "children": [],
                        },
                        {
                            "type": "directive",
                            "name": "locale-variant",
                            "options": {"locales": ["IN"]},
                            "children": [
                                {"type": "paragraph", "children": [{"type": "text", "value": "IN-only paragraph."}]}
                            ],
                        },
                    ],
                },
            }
        ],
    }
    p = tmp / "smoke.ast.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


def test_render_book_emits_typst(tmp_path: Path) -> None:
    ast_path = _make_manifest(tmp_path)
    out = tmp_path / "dist"
    result = render_book(ast_path=ast_path, out_dir=out, locale="en-IN", edition="2026.1")
    assert result.typst_path.exists()
    src = result.typst_path.read_text(encoding="utf-8")
    assert "Smoke" in src
    assert "IN-only paragraph" in src
    # provenance directive should be suppressed in print (rendered as Typst comment)
    assert "ai-provenance suppressed" in src
