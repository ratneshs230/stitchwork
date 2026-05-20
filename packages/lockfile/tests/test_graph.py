"""Lockfile graph tests."""

from pathlib import Path

from stitchwork_lockfile.graph import LockGraph, LockRecord


def test_round_trip(tmp_path: Path):
    g = LockGraph()
    g.add(LockRecord(kind="source", id="ch01", hash="abc"))
    g.add(LockRecord(kind="figure", id="fig-1", hash="def", deps=["ch01"]))
    p = tmp_path / "stitchwork.lock"
    g.save(p)
    g2 = LockGraph.load(p)
    assert len(g2.records) == 2
    assert g2.records["fig-1"].deps == ["ch01"]


def test_stale_propagation():
    g = LockGraph()
    g.add(LockRecord(kind="source", id="ch01", hash="v1"))
    g.add(LockRecord(kind="figure", id="fig-1", hash="f1", deps=["ch01"]))
    g.add(LockRecord(kind="figure", id="fig-2", hash="f2", deps=["ch01"]))
    # Source ch01 changes — both dependent figures must be flagged stale
    stale = g.stale({"ch01": "v2"})
    assert set(stale) == {"ch01", "fig-1", "fig-2"}


def test_unrelated_change_doesnt_invalidate():
    g = LockGraph()
    g.add(LockRecord(kind="source", id="ch01", hash="v1"))
    g.add(LockRecord(kind="source", id="ch02", hash="v1"))
    g.add(LockRecord(kind="figure", id="fig-2", hash="f", deps=["ch02"]))
    stale = g.stale({"ch01": "v2", "ch02": "v1"})
    assert "ch01" in stale
    assert "ch02" not in stale
    assert "fig-2" not in stale


def test_is_fresh():
    g = LockGraph()
    g.add(LockRecord(kind="source", id="ch01", hash="v1"))
    assert g.is_fresh("ch01", "v1") is True
    assert g.is_fresh("ch01", "v2") is False
    assert g.is_fresh("missing", "v1") is False
