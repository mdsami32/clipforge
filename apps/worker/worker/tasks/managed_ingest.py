"""Swap-in for INGEST_BACKEND=managed. Implement against whichever hosted
video-processing API you pick (Apify actor, Supadata, etc.) — must return the
same shape as the self-hosted path so pipeline.py doesn't care which backend
is active:

    download(url_or_object_key) -> local_video_path
    transcribe(local_video_path) -> (words, language)
"""
from ..config import settings


def download(source: str) -> str:
    raise NotImplementedError(
        "Wire this up to your chosen managed ingest API "
        f"(MANAGED_INGEST_API_KEY is {'set' if settings.managed_ingest_api_key else 'NOT set'})."
    )


def transcribe(local_video_path: str):
    raise NotImplementedError("Wire this up to your chosen managed transcription API.")
