"""Deterministic transcript-to-clip candidate generation."""

from dataclasses import dataclass
from math import isfinite
from typing import Any


_HOOK_TERMS = {
    "because", "best", "critical", "discover", "important", "learn",
    "mistake", "never", "problem", "secret", "truth", "why", "how",
    "lesson", "step", "wrong", "surprising", "changed", "simple",
}
_SENTENCE_ENDINGS = ".!?…"
_PUNCTUATION = set(",.!?;:%)]}")


@dataclass(frozen=True)
class TranscriptUnit:
    """A sentence-like, timestamp-safe unit that a clip may start or end on."""

    start: float
    end: float
    text: str
    words: tuple[dict[str, Any], ...]

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


def _time(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, parsed) if isfinite(parsed) else default


def _word_text(word: dict[str, Any]) -> str:
    return str(word.get("word", "")).strip()


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


def _sentence_boundary(word: dict[str, Any]) -> bool:
    return _word_text(word).endswith(tuple(_SENTENCE_ENDINGS))


def _gap(previous: dict[str, Any], current: dict[str, Any]) -> float:
    return max(0.0, _time(current.get("start")) - _time(previous.get("end")))


def _make_unit(words: list[dict[str, Any]], fallback_start: float = 0.0, fallback_end: float = 0.0, text: str | None = None) -> TranscriptUnit | None:
    valid_words = [word for word in words if _word_text(word)]
    if not valid_words and not text:
        return None
    start = _time(valid_words[0].get("start"), fallback_start) if valid_words else fallback_start
    end = _time(valid_words[-1].get("end"), fallback_end) if valid_words else fallback_end
    end = max(start, end)
    unit_text = text.strip() if text else _join_words([_word_text(word) for word in valid_words])
    if not unit_text:
        return None
    return TranscriptUnit(start=start, end=end, text=unit_text, words=tuple(valid_words))


def transcript_units(transcript: dict[str, Any], *, pause_gap: float = 0.8) -> list[TranscriptUnit]:
    """Split a canonical transcript on sentence punctuation and meaningful pauses."""
    units: list[TranscriptUnit] = []
    segments = transcript.get("segments", []) if isinstance(transcript, dict) else []
    for segment in segments or []:
        if not isinstance(segment, dict):
            continue
        segment_start = _time(segment.get("start"))
        segment_end = max(segment_start, _time(segment.get("end"), segment_start))
        raw_words = [word for word in (segment.get("words") or []) if isinstance(word, dict) and _word_text(word)]
        if not raw_words:
            unit = _make_unit([], segment_start, segment_end, str(segment.get("text", "")))
            if unit:
                units.append(unit)
            continue

        current: list[dict[str, Any]] = []
        for word in raw_words:
            if current and (_gap(current[-1], word) >= pause_gap):
                unit = _make_unit(current, segment_start, segment_end)
                if unit:
                    units.append(unit)
                current = []
            current.append(word)
            if _sentence_boundary(word):
                unit = _make_unit(current, segment_start, segment_end)
                if unit:
                    units.append(unit)
                current = []
        unit = _make_unit(current, segment_start, segment_end)
        if unit:
            units.append(unit)

    if units:
        return units

    # Keep the generator useful for minimal legacy fixtures that only provide
    # the flattened canonical word list.
    raw_words = [word for word in (transcript.get("words", []) if isinstance(transcript, dict) else []) if isinstance(word, dict)]
    unit = _make_unit(raw_words)
    return [unit] if unit else []


def _candidate_words(units: list[TranscriptUnit], start: int, end: int) -> list[dict[str, Any]]:
    return [word for unit in units[start : end + 1] for word in unit.words]


def _candidate_text(units: list[TranscriptUnit], start: int, end: int) -> str:
    return _join_words([unit.text for unit in units[start : end + 1]])


def _score(units: list[TranscriptUnit], start: int, end: int, target_duration: float) -> tuple[float, str]:
    words = _candidate_words(units, start, end)
    duration = max(0.01, units[end].end - units[start].start)
    tokens = [_word_text(word).lower().strip(",.!?;:%()[]{}") for word in words]
    opening_tokens = tokens[:10]
    hook_hits = sum(token in _HOOK_TERMS for token in opening_tokens)
    hook_score = min(1.0, hook_hits / 2.0)
    complete = 1.0 if units[end].text.rstrip().endswith(tuple(_SENTENCE_ENDINGS)) else 0.4
    confidences = [min(1.0, max(0.0, _time(word.get("confidence"), 0.8))) for word in words]
    confidence = sum(confidences) / len(confidences) if confidences else 0.75
    duration_score = max(0.0, 1.0 - abs(duration - target_duration) / max(target_duration, 1.0))
    gaps = sum(_gap(left, right) for left, right in zip(words, words[1:])) if len(words) > 1 else 0.0
    pacing = max(0.0, 1.0 - min(1.0, gaps / max(duration * 0.25, 0.01)))
    score = round(100.0 * (0.30 * hook_score + 0.25 * complete + 0.20 * confidence + 0.15 * duration_score + 0.10 * pacing), 2)

    reasons = []
    if hook_hits:
        reasons.append("a strong opening")
    if complete >= 1.0:
        reasons.append("a complete thought")
    if confidence >= 0.9:
        reasons.append("clear transcript timing")
    if pacing >= 0.8:
        reasons.append("tight pacing")
    rationale = "Deterministic candidate with " + (", ".join(reasons) if reasons else "a usable contiguous transcript window") + "."
    return score, rationale


def _title(text: str) -> str:
    compact = " ".join(text.split())
    if len(compact) > 57:
        compact = compact[:57].rsplit(" ", 1)[0].rstrip(" ,.!?;:") + "…"
    return compact or "Untitled clip"


def _overlap_ratio(left: dict[str, Any], right: dict[str, Any]) -> float:
    overlap = max(0.0, min(left["end_seconds"], right["end_seconds"]) - max(left["start_seconds"], right["start_seconds"]))
    shortest = max(0.01, min(left["end_seconds"] - left["start_seconds"], right["end_seconds"] - right["start_seconds"]))
    return overlap / shortest


def generate_clip_candidates(
    transcript: dict[str, Any],
    *,
    min_duration: float = 15.0,
    target_duration: float = 35.0,
    max_duration: float = 60.0,
    max_candidates: int = 10,
    pause_gap: float = 0.8,
) -> list[dict[str, Any]]:
    """Generate ranked, non-duplicative candidates without an external model."""
    if min_duration <= 0 or target_duration < min_duration or max_duration < target_duration:
        raise ValueError("candidate durations must satisfy 0 < min <= target <= max")
    units = transcript_units(transcript, pause_gap=pause_gap)
    if not units:
        return []

    raw_candidates: list[dict[str, Any]] = []
    for start in range(len(units)):
        end = start
        while end + 1 < len(units):
            next_duration = units[end + 1].end - units[start].start
            current_duration = units[end].end - units[start].start
            if current_duration >= min_duration and next_duration > max_duration:
                break
            end += 1
            if units[end].end - units[start].start >= target_duration:
                break
        duration = units[end].end - units[start].start
        if duration < min_duration and end + 1 < len(units):
            end += 1
            duration = units[end].end - units[start].start
        if duration <= 0:
            continue
        score, rationale = _score(units, start, end, target_duration)
        text = _candidate_text(units, start, end)
        raw_candidates.append({
            "title": _title(text),
            "rationale": rationale,
            "start_seconds": round(units[start].start, 3),
            "end_seconds": round(units[end].end, 3),
            "score": score,
        })

    if not raw_candidates:
        return []
    if len(units) == 1 or raw_candidates[0]["end_seconds"] - raw_candidates[0]["start_seconds"] < min_duration:
        return [raw_candidates[0]]

    selected: list[dict[str, Any]] = []
    for candidate in sorted(raw_candidates, key=lambda item: (-item["score"], item["start_seconds"])):
        if any(_overlap_ratio(candidate, existing) >= 0.60 for existing in selected):
            continue
        selected.append(candidate)
        if len(selected) >= max_candidates:
            break
    return selected
