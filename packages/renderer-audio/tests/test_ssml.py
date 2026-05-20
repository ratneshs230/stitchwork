"""SSML emission + WER tests."""

from stitchwork_renderer_audio.ssml import ast_to_ssml
from stitchwork_renderer_audio.qa import wer, strip_ssml


def test_ssml_emits_phoneme_for_ipa_pronounce():
    ast = {
        "type": "root",
        "children": [
            {
                "type": "paragraph",
                "children": [
                    {"type": "text", "value": "Say "},
                    {
                        "type": "role",
                        "name": "audio-pronounce",
                        "options": {"ipa": "/səbˈdʒuː.dɪ.tʃeɪ/"},
                        "text": "sub judice",
                    },
                    {"type": "text", "value": " aloud."},
                ],
            }
        ],
    }
    ssml = ast_to_ssml(ast, "T")
    assert '<phoneme alphabet="ipa"' in ssml
    assert "sub judice" in ssml


def test_ssml_emits_alias_for_alias_pronounce():
    ast = {
        "type": "root",
        "children": [
            {
                "type": "paragraph",
                "children": [
                    {
                        "type": "role",
                        "name": "audio-pronounce",
                        "options": {"alias": "doctor strange"},
                        "text": "Dr. Strange",
                    }
                ],
            }
        ],
    }
    ssml = ast_to_ssml(ast, "T")
    assert '<sub alias="doctor strange">Dr. Strange</sub>' in ssml


def test_provenance_and_visualref_are_suppressed():
    ast = {
        "type": "root",
        "children": [
            {"type": "directive", "name": "ai-provenance", "options": {"model": "x"}, "children": []},
            {"type": "directive", "name": "visual-ref", "options": {"role": "diagram", "id": "f", "alt": "x", "prompt": "p"}, "children": []},
            {"type": "paragraph", "children": [{"type": "text", "value": "Hello."}]},
        ],
    }
    ssml = ast_to_ssml(ast, "T")
    assert "ai-provenance" not in ssml
    assert "visual-ref" not in ssml
    assert "Hello." in ssml


def test_wer_basic():
    assert wer("the quick brown fox", "the quick brown fox") == 0.0
    score = wer("the quick brown fox", "the quick brown")
    assert score == 0.25  # one deletion in four words


def test_strip_ssml():
    s = '<speak><voice name="x"><p>Hello <emphasis>there</emphasis>.</p></voice></speak>'
    assert strip_ssml(s) == "Hello there."
