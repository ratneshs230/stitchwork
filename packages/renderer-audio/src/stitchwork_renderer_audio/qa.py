"""Whisper round-trip QA — WER computation."""

from __future__ import annotations
import re
from pathlib import Path
from typing import Any


def _normalise(text: str) -> list[str]:
    # Lowercase, strip punctuation, collapse whitespace
    cleaned = re.sub(r"[^\w\s']", " ", text.lower())
    return [w for w in re.split(r"\s+", cleaned) if w]


def wer(reference: str, hypothesis: str) -> float:
    """Levenshtein-based WER (word error rate)."""
    ref = _normalise(reference)
    hyp = _normalise(hypothesis)
    if not ref:
        return 1.0 if hyp else 0.0
    n, m = len(ref), len(hyp)
    # Edit-distance DP — O(n*m). Acceptable for chapter-scale comparisons.
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        curr = [i] + [0] * m
        for j in range(1, m + 1):
            if ref[i - 1] == hyp[j - 1]:
                curr[j] = prev[j - 1]
            else:
                curr[j] = 1 + min(prev[j], curr[j - 1], prev[j - 1])
        prev = curr
    return prev[m] / n


def strip_ssml(ssml: str) -> str:
    no_tags = re.sub(r"<[^>]+>", " ", ssml)
    return re.sub(r"\s+", " ", no_tags).strip()


def whisper_transcribe(audio_path: Path) -> dict[str, Any]:
    """Run Whisper large-v3 over the audio. Returns transcript + meta."""
    try:
        import whisper  # type: ignore
    except ImportError:
        return {"ok": False, "reason": "openai-whisper not installed"}
    model = whisper.load_model("large-v3")
    result = model.transcribe(str(audio_path))
    return {"ok": True, "text": result.get("text", ""), "lang": result.get("language")}


def round_trip(reference_ssml: str, audio_path: Path, threshold: float = 0.05) -> dict[str, Any]:
    reference_text = strip_ssml(reference_ssml)
    tx = whisper_transcribe(audio_path)
    if not tx.get("ok"):
        return {"ran": False, "reason": tx.get("reason"), "wer": None, "pass": None}
    score = wer(reference_text, tx["text"])
    return {
        "ran": True,
        "wer": score,
        "threshold": threshold,
        "pass": score <= threshold,
        "transcript_head": tx["text"][:400],
    }
