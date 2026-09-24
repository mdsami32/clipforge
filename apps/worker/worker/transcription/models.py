from typing import NotRequired, TypedDict


class TranscriptWord(TypedDict):
    word: str
    start: float
    end: float
    confidence: NotRequired[float]


class TranscriptSegment(TypedDict):
    id: int
    start: float
    end: float
    text: str
    words: list[TranscriptWord]


class NormalizedTranscript(TypedDict):
    version: int
    language: str | None
    duration: float
    segments: list[TranscriptSegment]
    words: list[TranscriptWord]
