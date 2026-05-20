"""JSON-LD ledger tests."""

from stitchwork_provenance.jsonld import build_provenance_ledger


def test_ledger_extracts_one_provenance():
    manifest = {
        "manifest": {"id": "x", "title": "X", "authors": ["A"]},
        "locale": "en-IN",
        "edition": "2026.1",
        "chapters": [
            {
                "id": "ch01",
                "ast": {
                    "type": "root",
                    "children": [
                        {
                            "type": "directive",
                            "name": "ai-provenance",
                            "options": {
                                "model": "claude-opus-4-7",
                                "prompt_hash": "abc123",
                                "generated_at": "2026-05-20T00:00:00Z",
                                "human_edits": "heavy",
                                "editor": "r.sharma",
                            },
                            "children": [],
                        },
                        {"type": "paragraph", "children": [{"type": "text", "value": "Hi."}]},
                    ],
                },
            }
        ],
    }
    ledger = build_provenance_ledger(manifest)
    parts = ledger["hasPart"]
    assert len(parts) == 1
    assert parts[0]["creator"]["name"] == "claude-opus-4-7"
    assert "EU AI Act Art. 50" in ledger["stitchwork:complianceCeiling"]
