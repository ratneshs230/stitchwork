"""Locale and edition filtering for Stitchwork AST.

A locale-variant block is included if its `locales` list contains the active
locale (or the active locale's primary tag prefix, e.g. `en-IN` → `IN`).
If no locale-variant in a chapter matches, all variants with `fallback: true`
are kept; if there is no fallback either, the entire variant group is dropped.

An edition block is included when the active edition version falls within
`since`/`until` (inclusive of `since`, exclusive of `until`). A `range`
option of the form "2026.1-2027.1" is also honoured.
"""

from __future__ import annotations
from typing import Any


def _ver_tuple(v: str) -> tuple[int, ...]:
    return tuple(int(p) for p in v.split("."))


def edition_includes(opts: dict[str, Any], active: str | None) -> bool:
    if active is None:
        return True
    av = _ver_tuple(active)
    since = opts.get("since")
    until = opts.get("until")
    range_ = opts.get("range")
    if range_ and "-" in range_:
        lo, hi = range_.split("-", 1)
        since = since or lo.strip()
        until = until or hi.strip()
    if since and av < _ver_tuple(since):
        return False
    if until and av >= _ver_tuple(until):
        return False
    return True


def locale_matches(opts: dict[str, Any], active: str | None) -> bool:
    if active is None:
        return True
    locales = opts.get("locales", [])
    primary = active.split("-")[0].upper()
    full = active.upper()
    for l in locales:
        lu = str(l).upper()
        if lu == full or lu == primary or full.startswith(lu + "-"):
            return True
    return False


def apply_filters(nodes: list[dict[str, Any]], locale: str | None, edition: str | None) -> list[dict[str, Any]]:
    """Return a new list of nodes with locale-variant/edition filtering applied recursively."""
    out: list[dict[str, Any]] = []
    # Two-pass for locale-variant groups: first see if any matches.
    # We treat consecutive locale-variant siblings as one group for fallback logic.
    i = 0
    while i < len(nodes):
        node = nodes[i]
        if isinstance(node, dict) and node.get("type") == "directive" and node.get("name") == "locale-variant":
            group: list[dict[str, Any]] = []
            while i < len(nodes) and isinstance(nodes[i], dict) and nodes[i].get("type") == "directive" and nodes[i].get("name") == "locale-variant":
                group.append(nodes[i])
                i += 1
            matched = [g for g in group if locale_matches(g.get("options", {}), locale)]
            if matched:
                chosen = matched
            else:
                chosen = [g for g in group if g.get("options", {}).get("fallback")]
            for g in chosen:
                g = dict(g)
                g["children"] = apply_filters(g.get("children", []), locale, edition)
                out.append(g)
            continue
        if isinstance(node, dict) and node.get("type") == "directive" and node.get("name") == "edition":
            if edition_includes(node.get("options", {}), edition):
                n = dict(node)
                n["children"] = apply_filters(n.get("children", []), locale, edition)
                out.append(n)
            i += 1
            continue
        if isinstance(node, dict) and "children" in node:
            n = dict(node)
            n["children"] = apply_filters(node["children"], locale, edition)
            out.append(n)
            i += 1
            continue
        out.append(node)
        i += 1
    return out
