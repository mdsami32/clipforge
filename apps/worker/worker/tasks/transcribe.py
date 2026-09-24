"""Word-level transcription via faster-whisper."""

from faster_whisper import WhisperModel

from ..config import settings
from ..transcription.normalize import normalize_transcript

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


def transcribe_timeline(local_video_path: str) -> dict:
    """Return the canonical transcript used by downstream Smart Clipping."""
    model = _get_model()
    segments, info = model.transcribe(local_video_path, word_timestamps=True)
    return normalize_transcript(
        segments,
        language=getattr(info, "language", None),
        duration=getattr(info, "duration", None),
    )


def transcribe(local_video_path: str) -> tuple[list[dict], str | None]:
    """Backward-compatible legacy helper returning words and language."""
    transcript = transcribe_timeline(local_video_path)
    return transcript["words"], transcript["language"]
