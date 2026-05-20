"""Filter unit tests for the Typst renderer."""

from stitchwork_renderer_typst.filters import edition_includes, locale_matches, apply_filters


def test_edition_since_only():
    assert edition_includes({"since": "2026.1"}, "2026.2") is True
    assert edition_includes({"since": "2026.1"}, "2026.0") is False


def test_edition_until_exclusive():
    assert edition_includes({"until": "2027.1"}, "2026.5") is True
    assert edition_includes({"until": "2027.1"}, "2027.1") is False


def test_edition_range():
    assert edition_includes({"range": "2026.1-2027.1"}, "2026.5") is True
    assert edition_includes({"range": "2026.1-2027.1"}, "2027.5") is False


def test_locale_primary_tag():
    assert locale_matches({"locales": ["IN"]}, "en-IN") is True
    assert locale_matches({"locales": ["US"]}, "en-IN") is False


def test_locale_no_filter_when_active_none():
    assert locale_matches({"locales": ["US"]}, None) is True


def test_apply_filters_drops_nonmatching_variant_no_fallback():
    nodes = [
        {"type": "directive", "name": "locale-variant", "options": {"locales": ["US"]}, "children": [{"type": "text", "value": "us"}]},
        {"type": "directive", "name": "locale-variant", "options": {"locales": ["UK"]}, "children": [{"type": "text", "value": "uk"}]},
    ]
    out = apply_filters(nodes, "en-IN", None)
    assert out == []


def test_apply_filters_keeps_matching_group():
    nodes = [
        {"type": "directive", "name": "locale-variant", "options": {"locales": ["IN"]}, "children": [{"type": "text", "value": "in"}]},
        {"type": "directive", "name": "locale-variant", "options": {"locales": ["US"]}, "children": [{"type": "text", "value": "us"}]},
    ]
    out = apply_filters(nodes, "en-IN", None)
    assert len(out) == 1
    assert out[0]["options"]["locales"] == ["IN"]


def test_apply_filters_uses_fallback_when_no_match():
    nodes = [
        {"type": "directive", "name": "locale-variant", "options": {"locales": ["US"]}, "children": [{"type": "text", "value": "us"}]},
        {"type": "directive", "name": "locale-variant", "options": {"locales": ["UK"], "fallback": True}, "children": [{"type": "text", "value": "uk-fallback"}]},
    ]
    out = apply_filters(nodes, "en-IN", None)
    assert len(out) == 1
    assert out[0]["options"]["fallback"] is True


def test_apply_filters_edition_drops_old():
    nodes = [
        {"type": "directive", "name": "edition", "options": {"since": "2027.1"}, "children": [{"type": "text", "value": "v2027"}]},
        {"type": "paragraph", "children": [{"type": "text", "value": "always"}]},
    ]
    out = apply_filters(nodes, None, "2026.1")
    assert len(out) == 1
    assert out[0]["type"] == "paragraph"
