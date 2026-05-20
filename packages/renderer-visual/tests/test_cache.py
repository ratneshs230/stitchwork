"""Content-hash cache tests."""

from pathlib import Path

from stitchwork_renderer_visual.cache import ContentHashCache, hash_spec


def test_hash_is_stable_across_key_order():
    a = hash_spec("mermaid", {"src": "X", "theme": "default"})
    b = hash_spec("mermaid", {"theme": "default", "src": "X"})
    assert a == b


def test_hash_differs_on_content_change():
    a = hash_spec("mermaid", {"src": "X"})
    b = hash_spec("mermaid", {"src": "Y"})
    assert a != b


def test_cache_round_trip(tmp_path: Path):
    cache = ContentHashCache(tmp_path)
    spec = {"src": "graph TD\nA --> B", "format": "svg"}
    entry = cache.entry("mermaid", spec, "svg")
    # Simulate worker producing output
    entry.artifact_path.write_text("<svg></svg>", encoding="utf-8")
    cache.commit(entry, "mermaid", spec)
    # Fetch into a new path
    dest = tmp_path / "out.svg"
    assert cache.fetch(entry, dest) is True
    assert dest.read_text(encoding="utf-8") == "<svg></svg>"


def test_cache_stats(tmp_path: Path):
    cache = ContentHashCache(tmp_path)
    entry = cache.entry("mermaid", {"x": 1}, "svg")
    entry.artifact_path.write_text("abc")
    cache.commit(entry, "mermaid", {"x": 1})
    s = cache.stats()
    assert s["entries"] == 1
    assert s["total_bytes"] > 0
