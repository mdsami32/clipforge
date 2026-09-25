from worker.candidates.generate import generate_clip_candidates, transcript_units


def _transcript(words):
    return {
        "version": 1,
        "language": "en",
        "duration": words[-1]["end"] if words else 0,
        "segments": [{
            "id": 0,
            "start": words[0]["start"] if words else 0,
            "end": words[-1]["end"] if words else 0,
            "text": " ".join(word["word"] for word in words),
            "words": words,
        }],
        "words": words,
    }


def _words(text, duration=2.0, confidence=0.95):
    tokens = text.split()
    step = duration / len(tokens)
    return [
        {"word": token, "start": round(index * step, 3), "end": round((index + 1) * step, 3), "confidence": confidence}
        for index, token in enumerate(tokens)
    ]


def test_units_split_on_sentence_punctuation():
    words = _words("Why does this matter? Because the simple lesson changed everything.", duration=4.0)
    units = transcript_units(_transcript(words))
    assert len(units) == 2
    assert units[0].text.endswith("?")
    assert units[1].text.endswith(".")


def test_units_split_on_pause_without_punctuation():
    words = [
        {"word": "First", "start": 0.0, "end": 0.5},
        {"word": "thought", "start": 0.6, "end": 1.0},
        {"word": "Second", "start": 2.0, "end": 2.5},
        {"word": "thought", "start": 2.6, "end": 3.0},
    ]
    assert len(transcript_units(_transcript(words), pause_gap=0.8)) == 2


def test_candidates_are_aligned_to_unit_boundaries_and_ranked():
    words = _words(
        "The problem is simple. This important lesson explains why you should never ignore it. "
        "The next step is practical. Because the best results require consistent work.",
        duration=32.0,
    )
    candidates = generate_clip_candidates(_transcript(words), min_duration=8, target_duration=16, max_duration=22)
    assert candidates
    assert all(candidate["start_seconds"] < candidate["end_seconds"] for candidate in candidates)
    assert all(0 <= candidate["score"] <= 100 for candidate in candidates)
    assert candidates == sorted(candidates, key=lambda item: item["score"], reverse=True)
    assert "complete thought" in candidates[0]["rationale"]


def test_candidates_deduplicate_heavily_overlapping_windows():
    words = _words("Why this matters. The important lesson is simple. Because the best step is consistency. Never skip the work.", duration=20.0)
    candidates = generate_clip_candidates(_transcript(words), min_duration=5, target_duration=10, max_duration=14, max_candidates=10)
    for index, left in enumerate(candidates):
        for right in candidates[index + 1:]:
            overlap = max(0, min(left["end_seconds"], right["end_seconds"]) - max(left["start_seconds"], right["start_seconds"]))
            shortest = min(left["end_seconds"] - left["start_seconds"], right["end_seconds"] - right["start_seconds"])
            assert overlap / shortest < 0.60


def test_empty_and_short_transcripts_are_safe():
    assert generate_clip_candidates({"segments": [], "words": []}) == []
    words = _words("Short clip.", duration=4.0)
    candidates = generate_clip_candidates(_transcript(words), min_duration=15, target_duration=35, max_duration=60)
    assert len(candidates) == 1
    assert candidates[0]["end_seconds"] == 4.0
