from worker.transcription.normalize import normalize_transcript


def test_empty_transcript_is_valid_and_empty():
    result = normalize_transcript([], language="en")

    assert result == {
        "version": 1,
        "language": "en",
        "duration": 0.0,
        "segments": [],
        "words": [],
    }


def test_overlapping_word_timestamps_are_preserved_as_float_seconds():
    result = normalize_transcript(
        [{
            "start": 1,
            "end": 4,
            "text": "One two",
            "words": [
                {"word": "One", "start": 1, "end": 2},
                {"word": "two", "start": 1.8, "end": 3},
            ],
        }],
        language="en",
    )

    assert result["segments"][0]["start"] == 1.0
    assert result["words"][1]["start"] == 1.8
    assert result["words"][0]["end"] > result["words"][1]["start"]


def test_malformed_words_are_skipped_without_dropping_valid_segment():
    result = normalize_transcript(
        [{
            "start": 2,
            "end": 5,
            "text": "hello",
            "words": [
                {"word": "hello", "start": 2, "end": 3, "probability": 0.9},
                {"word": "", "start": 3, "end": 4},
                {"start": "not-a-time", "end": 4},
            ],
        }]
    )

    assert len(result["segments"]) == 1
    assert [word["word"] for word in result["words"]] == ["hello"]
    assert result["words"][0]["confidence"] == 0.9


def test_missing_word_timestamps_are_estimated_inside_segment():
    result = normalize_transcript(
        [{"start": 10, "end": 14, "text": "hello world", "words": [{"word": "hello"}, {"word": "world"}]}]
    )

    assert [(word["start"], word["end"]) for word in result["words"]] == [(10.0, 12.0), (12.0, 14.0)]


def test_normal_transcript_preserves_text_language_confidence_and_duration():
    result = normalize_transcript(
        [{
            "start": 10.2,
            "end": 18.7,
            "text": "This is important.",
            "words": [
                {"word": "This", "start": 10.2, "end": 10.5, "probability": 0.98},
                {"word": "is", "start": 10.5, "end": 10.7, "probability": 0.97},
                {"word": "important.", "start": 11.0, "end": 11.8, "probability": 0.96},
            ],
        }],
        language=" en ",
        duration=123.4,
    )

    assert result["language"] == "en"
    assert result["duration"] == 123.4
    assert result["segments"][0]["text"] == "This is important."
    assert result["segments"][0]["words"][0]["confidence"] == 0.98
