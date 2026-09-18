"""Word-level timestamped transcription via faster-whisper (self-hosted).

Swap point: to use a hosted transcription API instead, implement the same
`transcribe(local_video_path) -> list[dict]` signature in managed_ingest.py
and switch on settings.ingest_backend in pipeline.py.
"""
from faster_whisper import WhisperModel

from ..config import settings

_model: WhisperModel | None = None


def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel(
            settings.whisper_model_size,
            device=settings.whisper_device,
            compute_type="int8" if settings.whisper_device == "cpu" else "float16",
        )
    return _model


def transcribe(local_video_path: str) -> tuple[list[dict], str]:
    """Returns (word_level_segments, detected_language).

    word_level_segments: [{"word": str, "start": float, "end": float}, ...]
    """
    model = _get_model()
    segments, info = model.transcribe(local_video_path, word_timestamps=True)

    words = []
    for segment in segments:
        for w in segment.words or []:
            words.append({"word": w.word.strip(), "start": w.start, "end": w.end})

    return words, info.language
