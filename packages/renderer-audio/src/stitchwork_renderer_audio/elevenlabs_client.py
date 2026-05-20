"""ElevenLabs Projects API client (best-effort)."""

from __future__ import annotations
import os
import time
from pathlib import Path
from typing import Any


def _have_client() -> tuple[bool, str | None]:
    if not os.environ.get("ELEVENLABS_API_KEY"):
        return False, "ELEVENLABS_API_KEY not set"
    try:
        import elevenlabs  # noqa: F401  # type: ignore
        return True, None
    except ImportError:
        return False, "elevenlabs python package not installed"


def synthesize_chapter(ssml: str, out_path: Path, voice_id: str, model_id: str = "eleven_multilingual_v2") -> dict[str, Any]:
    """Synthesize a single chapter SSML via the ElevenLabs Text-to-Speech endpoint.

    For the Projects API (multi-chapter workflows) this routes via ``client.projects.add``;
    that path is reserved for full books. Single-chapter renders use the standard TTS
    endpoint with `output_format=mp3_44100_128`.
    """
    ok, reason = _have_client()
    if not ok:
        return {"ok": False, "reason": reason}
    from elevenlabs.client import ElevenLabs  # type: ignore

    client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
    audio_iter = client.text_to_speech.convert(
        voice_id=voice_id,
        model_id=model_id,
        text=ssml,
        output_format="mp3_44100_128",
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("wb") as f:
        for chunk in audio_iter:
            if chunk:
                f.write(chunk)
    return {"ok": True, "path": str(out_path), "bytes": out_path.stat().st_size}


def synthesize_project(
    chapters: list[dict[str, Any]],
    project_name: str,
    voice_narration: str,
    voice_quote: str | None = None,
    poll_interval_s: float = 15.0,
    max_wait_s: float = 1800.0,
) -> dict[str, Any]:
    """Submit a full project to ElevenLabs Projects API and wait for completion."""
    ok, reason = _have_client()
    if not ok:
        return {"ok": False, "reason": reason}
    from elevenlabs.client import ElevenLabs  # type: ignore

    client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
    # Newer SDKs expose `projects.create`; older expose `projects.add`. We try both.
    api = getattr(client, "projects", None)
    if api is None:
        return {"ok": False, "reason": "elevenlabs SDK has no projects API"}
    create = getattr(api, "create", None) or getattr(api, "add", None)
    if create is None:
        return {"ok": False, "reason": "elevenlabs projects.create not available in this SDK"}

    project = create(
        name=project_name,
        default_title_voice_id=voice_narration,
        default_paragraph_voice_id=voice_quote or voice_narration,
        from_document=False,
    )
    project_id = getattr(project, "project_id", None) or getattr(project, "id", None)

    # Upload chapter SSML
    upload = getattr(api, "add_chapter", None) or getattr(api, "chapter_add", None)
    if upload is None:
        return {"ok": False, "reason": "elevenlabs projects.add_chapter not available", "project_id": project_id}
    for ch in chapters:
        upload(project_id=project_id, name=ch["title"], from_text=ch["ssml"])

    # Trigger conversion and poll
    convert = getattr(api, "convert", None) or getattr(api, "start_conversion", None)
    if convert is None:
        return {"ok": False, "reason": "elevenlabs projects.convert not available", "project_id": project_id}
    convert(project_id=project_id)

    elapsed = 0.0
    status = "pending"
    get = getattr(api, "get", None) or getattr(api, "retrieve", None)
    while elapsed < max_wait_s and status not in ("done", "failed"):
        time.sleep(poll_interval_s)
        elapsed += poll_interval_s
        if get is None:
            break
        p = get(project_id=project_id)
        status = getattr(p, "state", None) or getattr(p, "status", "unknown")
    return {"ok": status == "done", "project_id": project_id, "status": status, "elapsed_s": elapsed}
