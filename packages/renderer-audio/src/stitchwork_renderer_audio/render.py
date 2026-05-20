"""End-to-end audiobook render driver."""

from __future__ import annotations
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .ssml import ast_to_ssml
from .qa import round_trip


@dataclass
class AudioRenderResult:
    out_dir: Path
    ssml_paths: list[Path]
    mp3_paths: list[Path]
    qa: dict[str, Any]
    ok: bool
    notes: list[str]


def render_audiobook(
    ast_path: Path,
    out_dir: Path,
    *,
    voice_narration: str | None = None,
    voice_quote: str | None = None,
    locale: str | None = None,
    edition: str | None = None,
    wer_threshold: float = 0.05,
) -> AudioRenderResult:
    manifest = json.loads(ast_path.read_text(encoding="utf-8"))
    book = manifest["manifest"]
    locale = locale or manifest.get("locale", "en-IN")
    out_dir.mkdir(parents=True, exist_ok=True)
    notes: list[str] = []

    # Apply locale/edition filters using the typst filter (single source of truth)
    try:
        from stitchwork_renderer_typst.filters import apply_filters  # type: ignore
    except ImportError:
        apply_filters = None  # type: ignore

    voice_narration = voice_narration or os.environ.get("STITCHWORK_VOICE_NARRATION", "default-narration")
    voice_quote = voice_quote or os.environ.get("STITCHWORK_VOICE_QUOTE", "default-quote")

    ssml_paths: list[Path] = []
    mp3_paths: list[Path] = []
    qa_report: dict[str, Any] = {}

    for ch in manifest.get("chapters", []):
        ast = ch["ast"]
        if apply_filters is not None:
            ast = dict(ast)
            ast["children"] = apply_filters(ast.get("children", []), locale, edition)
        title = book.get("title", ch["id"])
        ssml = ast_to_ssml(ast, title, voice_narration, voice_quote, lang=locale)
        ssml_path = out_dir / f"{ch['id']}.ssml.xml"
        ssml_path.write_text(ssml, encoding="utf-8")
        ssml_paths.append(ssml_path)

        # Synthesis (best-effort, gated on env)
        if os.environ.get("ELEVENLABS_API_KEY"):
            from .elevenlabs_client import synthesize_chapter

            mp3_path = out_dir / f"{ch['id']}.mp3"
            res = synthesize_chapter(ssml, mp3_path, voice_narration)
            if res.get("ok"):
                mp3_paths.append(mp3_path)
                qa = round_trip(ssml, mp3_path, threshold=wer_threshold)
                qa_report[ch["id"]] = qa
            else:
                notes.append(f"{ch['id']}: synthesis skipped — {res.get('reason')}")
        else:
            notes.append("ELEVENLABS_API_KEY not set; emitted SSML only")

    # Aggregate pass/fail
    qa_pass = all(q.get("pass", True) for q in qa_report.values()) if qa_report else None
    return AudioRenderResult(
        out_dir=out_dir,
        ssml_paths=ssml_paths,
        mp3_paths=mp3_paths,
        qa={"per_chapter": qa_report, "all_pass": qa_pass},
        ok=qa_pass is not False,
        notes=notes,
    )
