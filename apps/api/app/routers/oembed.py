"""YouTube oEmbed preview — no API key required.

Called by the frontend the moment a user pastes a YouTube URL, so the title +
thumbnail render instantly while the actual download/transcribe job runs in
the background.
"""
import httpx
from fastapi import APIRouter, HTTPException, Query

from ..schemas import OEmbedPreview

router = APIRouter(prefix="/oembed", tags=["oembed"])

YOUTUBE_OEMBED_URL = "https://www.youtube.com/oembed"


@router.get("/youtube", response_model=OEmbedPreview)
def youtube_oembed(url: str = Query(..., description="Full YouTube video URL")):
    try:
        resp = httpx.get(YOUTUBE_OEMBED_URL, params={"url": url, "format": "json"}, timeout=5)
        resp.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch oEmbed preview: {e}")

    data = resp.json()
    return OEmbedPreview(
        title=data["title"],
        author_name=data.get("author_name", ""),
        thumbnail_url=data["thumbnail_url"],
        provider_name=data.get("provider_name", "YouTube"),
    )
