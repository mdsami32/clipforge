"""Normalize transcription providers into ClipForge's canonical timeline."""

from collections.abc import Iterable, Mapping
from math import isfinite
from typing import Any

from .models import NormalizedTranscript, TranscriptWord


_PUNCTUATION = set(",.!?;:%)]}")


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def _time(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not isfinite(parsed):
        return None
    return max(0.0, parsed)


def _confidence(value: Any) -> float | None:
    parsed = _time(value)
    if parsed is None:
        return None
    return min(1.0, parsed)


def _join_words(words: list[str]) -> str:
    text = ""
    for token in words:
        token = token.strip()
        if not token:
            continue
        if not text or token[0] in _PUNCTUATION or token in {"'s", "'t", "n't"}:
            text += token
        elif text[-1] in "([{":
            text += token
        else:
            text += " " + token
    return text


def _raw_word(raw_word: Any) -> tuple[str, float | None, float | None, float | None] | None:
    raw_text = _get(raw_word, "word")
    if raw_text is None:
        return None
    text = str(raw_text).strip()
    if not text:
        return None

    raw_confidence = _get(raw_word, "confidence")
    if raw_confidence is None:
        raw_confidence = _get(raw_word, "probability")

    return (text, _time(_get(raw_word, "start")), _time(_get(raw_word, "end")), _confidence(raw_confidence))


def normalize_transcript(raw_segments: Iterable[Any] | None, *, language: str | None = None, duration: Any = None) -> NormalizedTranscript:
    """Return stable JSON data from dictionaries or faster-whisper objects."""
    normalized_segments = []

    for raw_segment in raw_segments or []:
        raw_words = list(_get(raw_segment, "words", []) or [])
        parsed_words = [parsed for raw_word in raw_words if (parsed := _raw_word(raw_word))]
        raw_start = _time(_get(raw_segment, "start"))
        raw_end = _time(_get(raw_segment, "end"))

        timed_starts = [word[1] for word in parsed_words if word[1] is not None]
        timed_ends = [word[2] for word in parsed_words if word[2] is not None]
        start = raw_start if raw_start is not None else (min(timed_starts) if timed_starts else None)
        end = raw_end if raw_end is not None else (max(timed_ends) if timed_ends else None)

        if start is None and end is None:
            if not parsed_words:
                continue
            start, end = 0.0, float(len(parsed_words))
        elif start is None:
            start = max(0.0, end - 1.0)
        elif end is None:
            end = start
        end = max(start, end)

        span = end - start
        count = max(1, len(parsed_words))
        words: list[TranscriptWord] = []
        for index, (text, word_start, word_end, confidence) in enumerate(parsed_words):
            estimate_start = start + span * index / count
            estimate_end = start + span * (index + 1) / count
            word_start = estimate_start if word_start is None else word_start
            word_end = estimate_end if word_end is None else word_end
            if word_end < word_start:
                word_end = word_start

            normalized_word: TranscriptWord = {"word": text, "start": float(max(0.0, word_start)), "end": float(max(0.0, word_end))}
            if confidence is not None:
                normalized_word["confidence"] = confidence
            words.append(normalized_word)

        if words:
            start = min(start, min(word["start"] for word in words))
            end = max(end, max(word["end"] for word in words))

        raw_text = _get(raw_segment, "text")
        text = str(raw_text).strip() if raw_text is not None else ""
        if not text:
            text = _join_words([word["word"] for word in words])
        if not text and not words:
            continue

        normalized_segments.append({"id": len(normalized_segments), "start": float(start), "end": float(end), "text": text, "words": words})

    flattened_words: list[TranscriptWord] = [word for segment in normalized_segments for word in segment["words"]]
    requested_duration = _time(duration)
    observed_duration = max([segment["end"] for segment in normalized_segments] + [word["end"] for word in flattened_words] + [0.0])

    return {
        "version": 1,
        "language": language.strip() if isinstance(language, str) and language.strip() else None,
        "duration": float(max(requested_duration or 0.0, observed_duration)),
        "segments": normalized_segments,
        "words": flattened_words,
    }


def normalize_word_list(words: Iterable[Any] | None, *, language: str | None = None, duration: Any = None) -> NormalizedTranscript:
    """Adapt legacy managed-ingest word-list output."""
    raw_words = list(words or [])
    word_text, starts, ends = [], [], []
    for raw_word in raw_words:
        parsed = _raw_word(raw_word)
        if not parsed:
            continue
        word_text.append(parsed[0])
        if parsed[1] is not None:
            starts.append(parsed[1])
        if parsed[2] is not None:
            ends.append(parsed[2])

    segment = {"start": min(starts) if starts else 0.0, "end": max(ends) if ends else (_time(duration) or 0.0), "text": _join_words(word_text), "words": raw_words}
    return normalize_transcript([segment] if word_text else [], language=language, duration=duration)
