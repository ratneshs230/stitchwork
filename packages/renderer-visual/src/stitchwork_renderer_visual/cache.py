"""Content-hash cache for the visual pipeline."""

from __future__ import annotations
import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def hash_spec(worker: str, spec: dict[str, Any]) -> str:
    payload = canonical_json({"w": worker, "s": spec}).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass
class CacheEntry:
    key: str
    artifact_path: Path
    meta_path: Path


class ContentHashCache:
    """Cache by sha-256 of canonical-JSON spec.

    Layout::

        .stitchwork-cache/
          visual/
            <key>/
              meta.json       — worker, spec, content_type, size, mtime
              artifact.<ext>  — the actual rendered file
    """

    def __init__(self, root: Path) -> None:
        self.root = root / "visual"
        self.root.mkdir(parents=True, exist_ok=True)

    def entry(self, worker: str, spec: dict[str, Any], extension: str) -> CacheEntry:
        key = hash_spec(worker, spec)
        d = self.root / key
        d.mkdir(parents=True, exist_ok=True)
        return CacheEntry(
            key=key,
            artifact_path=d / f"artifact.{extension.lstrip('.')}",
            meta_path=d / "meta.json",
        )

    def exists(self, entry: CacheEntry) -> bool:
        return entry.artifact_path.exists() and entry.meta_path.exists()

    def commit(self, entry: CacheEntry, worker: str, spec: dict[str, Any]) -> None:
        meta = {
            "worker": worker,
            "spec": spec,
            "size": entry.artifact_path.stat().st_size if entry.artifact_path.exists() else 0,
            "version": 1,
        }
        entry.meta_path.write_text(canonical_json(meta), encoding="utf-8")

    def fetch(self, entry: CacheEntry, dest: Path) -> bool:
        if not self.exists(entry):
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(entry.artifact_path, dest)
        return True

    def evict(self, key: str) -> None:
        d = self.root / key
        if d.exists():
            shutil.rmtree(d)

    def stats(self) -> dict[str, Any]:
        keys = [p.name for p in self.root.iterdir() if p.is_dir()]
        total_bytes = 0
        for k in keys:
            artefacts = list((self.root / k).glob("artifact.*"))
            for a in artefacts:
                try:
                    total_bytes += a.stat().st_size
                except OSError:
                    pass
        return {"entries": len(keys), "total_bytes": total_bytes, "root": str(self.root)}
