"""Stitchwork provenance emission."""

__version__ = "0.1.0"

from .jsonld import build_provenance_ledger
from .c2pa import emit_c2pa_sidecar
from .iptc import write_iptc_ai_fields

__all__ = ["build_provenance_ledger", "emit_c2pa_sidecar", "write_iptc_ai_fields", "__version__"]
