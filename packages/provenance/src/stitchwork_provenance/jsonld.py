"""JSON-LD provenance ledger emission.

Schema: combines schema.org CreativeWork properties with the C2PA "stds.schema-org"
shape so the ledger plugs into both EPUB metadata consumers and generic linked-data tools.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any


def _collect_provenance(ast: dict[str, Any], chapter_id: str, out: list[dict[str, Any]]) -> None:
    if not isinstance(ast, dict):
        return
    if ast.get("type") == "directive" and ast.get("name") == "ai-provenance":
        opts = ast.get("options", {})
        out.append({
            "@type": "CreativeWork",
            "identifier": f"sw:prov:{chapter_id}:{len(out)}",
            "inLocation": chapter_id,
            "creator": {
                "@type": "SoftwareApplication",
                "name": opts.get("model"),
                "softwareVersion": opts.get("model"),
            },
            "dateCreated": opts.get("generated_at"),
            "creativeWorkStatus": opts.get("human_edits"),
            "editor": opts.get("editor"),
            "isBasedOn": {
                "@type": "DigitalDocument",
                "encodingFormat": "text/markdown",
            },
            "additionalProperty": [{
                "@type": "PropertyValue",
                "propertyID": "stitchwork:promptHash",
                "value": opts.get("prompt_hash"),
            }],
        })
    for child in ast.get("children", []) or []:
        _collect_provenance(child, chapter_id, out)


def build_provenance_ledger(manifest: dict[str, Any]) -> dict[str, Any]:
    book = manifest["manifest"]
    records: list[dict[str, Any]] = []
    for ch in manifest.get("chapters", []):
        _collect_provenance(ch["ast"], ch["id"], records)
    ledger = {
        "@context": [
            "https://schema.org",
            {"stitchwork": "https://stitchwork.dev/vocab#"},
        ],
        "@type": "Book",
        "identifier": book.get("isbn", {}).get("ebook") or book["id"],
        "name": book.get("title"),
        "author": [{"@type": "Person", "name": a} for a in book.get("authors", []) or []],
        "inLanguage": (manifest.get("locale") or "en").split("-")[0],
        "stitchwork:edition": manifest.get("edition"),
        "stitchwork:locale": manifest.get("locale"),
        "stitchwork:complianceCeiling": ["EU AI Act Art. 50", "India IT Rules 2026"],
        "hasPart": records,
    }
    return ledger


def emit_ledger(manifest: dict[str, Any], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    ledger = build_provenance_ledger(manifest)
    p = out_dir / "provenance.jsonld"
    p.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    return p
