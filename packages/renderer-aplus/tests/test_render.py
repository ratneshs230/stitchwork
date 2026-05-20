"""A+ renderer tests."""

from pathlib import Path

from stitchwork_renderer_aplus.render import render_aplus


def _manifest():
    return {
        "manifest": {
            "id": "sample",
            "title": "Sample Title",
            "subtitle": "A pithy subtitle",
            "authors": ["Alice", "Bob"],
        },
        "chapters": [
            {
                "id": "ch01",
                "ast": {
                    "type": "root",
                    "children": [
                        {"type": "heading", "depth": 1, "children": [{"type": "text", "value": "Intro"}]},
                        {"type": "paragraph", "children": [{"type": "text", "value": "Opening paragraph one two three four five."}]},
                        {
                            "type": "directive", "name": "practitioner-quote",
                            "options": {"source_name": "P", "role": "Pro", "jurisdiction": "IN", "consent_id": "c", "rev_share_bps": 50},
                            "children": [{"type": "paragraph", "children": [{"type": "text", "value": "Quoted body."}]}],
                        },
                        {
                            "type": "directive", "name": "visual-ref",
                            "options": {"role": "infographic", "id": "fig-x", "alt": "An infographic.", "prompt": "p"},
                            "children": [],
                        },
                    ],
                },
            }
        ],
    }


def test_render_aplus_emits_modules(tmp_path: Path):
    res = render_aplus(_manifest(), tmp_path)
    modules = [m["module"] for m in res.modules]
    assert "STANDARD_HEADER_IMAGE_TEXT" in modules
    assert "STANDARD_TEXT_BLOCK" in modules
    assert "STANDARD_QUOTE" in modules
    assert "STANDARD_IMAGE_TEXT_OVERLAY" in modules
    assert (tmp_path / "index.json").exists()
    assert (tmp_path / "01-header.html").exists()
