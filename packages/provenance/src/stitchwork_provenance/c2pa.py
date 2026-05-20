"""C2PA sidecar emission.

When `py-c2pa` is available we attach a real attestation. Otherwise we emit a
parseable JSON-stub with the same key fields so the downstream provenance ledger
still references something tangible.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any


def emit_c2pa_sidecar(image_path: Path, manifest: dict[str, Any]) -> Path:
    """Write image_path.c2pa next to image_path with the attestation manifest.

    manifest = {
      "claim_generator": "stitchwork/0.1.0",
      "format": "image/png",
      "actions": [{"action": "c2pa.created", "softwareAgent": "imagen-4"}, ...],
      "assertions": [...],
    }
    """
    sidecar = image_path.with_suffix(image_path.suffix + ".c2pa")
    try:
        import c2pa  # type: ignore
        builder = c2pa.ManifestBuilder(json.dumps(manifest))
        builder.sign(str(image_path), str(sidecar))
        return sidecar
    except ImportError:
        # Stub mode — emit JSON. Downstream tooling can still consume.
        sidecar.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return sidecar
