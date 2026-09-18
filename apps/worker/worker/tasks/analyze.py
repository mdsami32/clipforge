"""AI highlight detection: given the full word-level transcript, ask an LLM
to propose ranked clip candidates (title, rationale, start/end timestamps).

Uses the Claude Messages API directly (see packages' README for swapping to
another provider). Structured output is enforced by instructing the model to
return JSON only, then parsed defensively.
"""
import json
import re

import httpx

from ..config import settings

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

SYSTEM_PROMPT = """You are a short-form video producer. You are given a
word-level transcript (word, start_seconds, end_seconds) of a longer video.
Identify the 5-10 best segments to turn into standalone vertical short-form
clips (30-90 seconds each, non-overlapping, in chronological order).

For each candidate return:
- title: a punchy, specific title (<=60 chars)
- rationale: one sentence on why this moment will hook viewers
- start_seconds / end_seconds: aligned to natural sentence boundaries in the transcript
- score: 0-100, your confidence this clip performs well

Respond with ONLY a JSON array of objects with keys:
title, rationale, start_seconds, end_seconds, score. No prose, no markdown fences."""


def _transcript_to_compact_text(words: list[dict]) -> str:
    # Compact "word[start-end]" stream keeps the prompt small while preserving
    # exact timestamps the model can reference back.
    return " ".join(f"{w['word']}[{w['start']:.1f}-{w['end']:.1f}]" for w in words)


def find_highlight_candidates(words: list[dict]) -> list[dict]:
    if not settings.llm_api_key:
        # No key configured: fall back to naive fixed-window segmentation so
        # the rest of the pipeline (and the UI) still has something to show.
        return _fallback_fixed_windows(words)

    transcript_text = _transcript_to_compact_text(words)
    payload = {
        "model": settings.llm_model,
        "max_tokens": 2000,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": transcript_text[:60000]}],
    }
    headers = {
        "x-api-key": settings.llm_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    resp = httpx.post(ANTHROPIC_API_URL, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    text = "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")

    try:
        candidates = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        candidates = json.loads(match.group(0)) if match else []

    return candidates or _fallback_fixed_windows(words)


def _fallback_fixed_windows(words: list[dict], window_seconds: float = 45.0) -> list[dict]:
    if not words:
        return []
    total_end = words[-1]["end"]
    candidates = []
    t = 0.0
    i = 1
    while t < total_end:
        end = min(t + window_seconds, total_end)
        candidates.append(
            {
                "title": f"Clip {i}",
                "rationale": "Auto-generated fallback segment (no LLM_API_KEY configured).",
                "start_seconds": t,
                "end_seconds": end,
                "score": 50,
            }
        )
        t += window_seconds
        i += 1
    return candidates
