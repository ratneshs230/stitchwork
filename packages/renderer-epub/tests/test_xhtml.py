"""Smoke tests for XHTML emission."""

from stitchwork_renderer_epub.xhtml import chapter_to_xhtml


def test_heading_and_paragraph():
    ast = {
        "type": "root",
        "children": [
            {"type": "heading", "depth": 1, "id": "intro", "children": [{"type": "text", "value": "Intro"}]},
            {"type": "paragraph", "children": [{"type": "text", "value": "Hello "}, {"type": "strong", "children": [{"type": "text", "value": "world"}]}, {"type": "text", "value": "."}]},
        ],
    }
    html = chapter_to_xhtml(ast, "Intro")
    assert '<h1 id="intro">Intro</h1>' in html
    assert "<strong>world</strong>" in html


def test_directive_emission():
    ast = {
        "type": "root",
        "children": [
            {
                "type": "directive",
                "name": "practitioner-quote",
                "options": {
                    "source_name": "Q",
                    "role": "R",
                    "jurisdiction": "IN",
                    "consent_id": "c1",
                    "rev_share_bps": 50,
                },
                "children": [
                    {"type": "paragraph", "children": [{"type": "text", "value": "Body."}]}
                ],
            },
            {
                "type": "directive",
                "name": "workbook-prompt",
                "options": {"id": "x", "kind": "fill", "lines": 3},
                "children": [{"type": "paragraph", "children": [{"type": "text", "value": "Prompt."}]}],
            },
        ],
    }
    html = chapter_to_xhtml(ast, "T")
    assert 'role="doc-pullquote"' in html
    assert 'data-rev-share-bps="50"' in html
    assert 'role="form"' in html
    assert html.count('class="sw-wb-line"') == 3


def test_inline_roles():
    ast = {
        "type": "root",
        "children": [
            {
                "type": "paragraph",
                "children": [
                    {
                        "type": "role",
                        "name": "regulatory-cite",
                        "options": {"jurisdiction": "IN", "source_url": "https://x", "statute": "S"},
                        "text": "the rule",
                    },
                    {"type": "text", "value": " applies."},
                ],
            }
        ],
    }
    html = chapter_to_xhtml(ast, "T")
    assert 'class="sw-cite"' in html
    assert 'href="https://x"' in html
