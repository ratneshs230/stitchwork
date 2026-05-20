"""Content-hash dependency graph."""

from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Iterable


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class LockRecord:
    kind: str
    id: str
    hash: str
    deps: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)


class LockGraph:
    def __init__(self) -> None:
        self.records: dict[str, LockRecord] = {}

    @classmethod
    def load(cls, path: Path) -> "LockGraph":
        g = cls()
        if not path.exists():
            return g
        for raw in path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw or raw.startswith("#"):
                continue
            obj = json.loads(raw)
            r = LockRecord(**obj)
            g.records[r.id] = r
        return g

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps(asdict(r), sort_keys=True, ensure_ascii=False) for r in self.records.values()]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def add(self, record: LockRecord) -> None:
        self.records[record.id] = record

    def is_fresh(self, record_id: str, new_hash: str) -> bool:
        existing = self.records.get(record_id)
        if existing is None:
            return False
        if existing.hash != new_hash:
            return False
        for dep_id in existing.deps:
            dep = self.records.get(dep_id)
            if dep is None:
                return False
        return True

    def stale(self, current_hashes: dict[str, str]) -> list[str]:
        """Return IDs whose hash (or any transitive dep hash) has changed."""
        stale_set: set[str] = set()
        # Direct hash mismatch
        for rid, new_hash in current_hashes.items():
            rec = self.records.get(rid)
            if rec is None or rec.hash != new_hash:
                stale_set.add(rid)
        # Propagate to dependents
        changed = True
        while changed:
            changed = False
            for r in self.records.values():
                if r.id in stale_set:
                    continue
                if any(d in stale_set for d in r.deps):
                    stale_set.add(r.id)
                    changed = True
        return sorted(stale_set)

    def iter_kind(self, kind: str) -> Iterable[LockRecord]:
        for r in self.records.values():
            if r.kind == kind:
                yield r
