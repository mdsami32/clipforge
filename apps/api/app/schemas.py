import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class ProjectCreateFromURL(BaseModel):
    youtube_url: str


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    source_type: str
    source_url: str | None = None
    thumbnail_url: str | None = None
    duration_seconds: float | None = None
    status: str
    error_message: str | None = None


class OEmbedPreview(BaseModel):
    title: str
    author_name: str
    thumbnail_url: str
    provider_name: str


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_id: uuid.UUID
    job_type: str
    status: str
    progress: int
    error_message: str | None = None


class TranscriptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_id: uuid.UUID
    transcript: dict[str, Any]
    words: list[dict[str, Any]]
    language: str | None = None


class ClipCandidateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    rationale: str
    start_seconds: float
    end_seconds: float
    score: float | None = None
    thumbnail_url: str | None = None


class ClipCreateFromCandidate(BaseModel):
    candidate_id: uuid.UUID


class ClipUpdate(BaseModel):
    title: str | None = None
    start_seconds: float | None = None
    end_seconds: float | None = None
    crop_box: dict[str, Any] | None = None
    face_track_enabled: bool | None = None
    captions: list[dict[str, Any]] | None = None
    caption_style: dict[str, Any] | None = None
    hook_text: list[dict[str, Any]] | None = None
    audio_settings: dict[str, Any] | None = None
    preset_id: uuid.UUID | None = None


class ClipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    start_seconds: float
    end_seconds: float
    crop_box: dict[str, Any] | None = None
    face_track_enabled: bool
    captions: list[dict[str, Any]] | None = None
    caption_style: dict[str, Any] | None = None
    hook_text: list[dict[str, Any]] | None = None
    audio_settings: dict[str, Any] | None = None
    render_status: str
    rendered_preview_url: str | None = None
    preset_id: uuid.UUID | None = None


class PresetCreate(BaseModel):
    name: str
    platform: Literal["youtube", "tiktok", "instagram"] | None = None
    resolution_w: int = 1080
    resolution_h: int = 1920
    bitrate_kbps: int = 8000
    caption_style: dict[str, Any] | None = None
    safe_zone_margins: dict[str, Any] | None = None
    is_default: bool = False


class PresetOut(PresetCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
