import uuid
from datetime import datetime

from sqlalchemy import (JSON, TIMESTAMP, Enum, ForeignKey, Numeric,
                         SmallInteger, String, Text, create_engine)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (DeclarativeBase, Mapped, mapped_column,
                             relationship, sessionmaker)

from .config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def _uuid_col():
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[uuid.UUID] = _uuid_col()
    title: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(Enum("youtube_url", "upload", name="ingest_source"))
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_object_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("pending", "running", "succeeded", "failed", name="job_status"), default="pending"
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    jobs: Mapped[list["Job"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    clip_candidates: Mapped[list["ClipCandidate"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    clips: Mapped[list["Clip"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[uuid.UUID] = _uuid_col()
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    job_type: Mapped[str] = mapped_column(String)  # download | transcribe | analyze | render
    status: Mapped[str] = mapped_column(
        Enum("pending", "running", "succeeded", "failed", name="job_status"), default="pending"
    )
    progress: Mapped[int] = mapped_column(SmallInteger, default=0)
    rq_job_id: Mapped[str | None] = mapped_column(String, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="jobs")


class Transcript(Base):
    __tablename__ = "transcripts"
    id: Mapped[uuid.UUID] = _uuid_col()
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    transcript: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    words: Mapped[list] = mapped_column(JSON)  # legacy flattened compatibility field
    language: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)


class ClipCandidate(Base):
    __tablename__ = "clip_candidates"
    id: Mapped[uuid.UUID] = _uuid_col()
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(Text)
    rationale: Mapped[str] = mapped_column(Text)
    start_seconds: Mapped[float] = mapped_column(Numeric)
    end_seconds: Mapped[float] = mapped_column(Numeric)
    score: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="clip_candidates")


class Preset(Base):
    __tablename__ = "presets"
    id: Mapped[uuid.UUID] = _uuid_col()
    name: Mapped[str] = mapped_column(Text)
    platform: Mapped[str | None] = mapped_column(
        Enum("youtube", "tiktok", "instagram", name="publish_platform"), nullable=True
    )
    resolution_w: Mapped[int] = mapped_column(default=1080)
    resolution_h: Mapped[int] = mapped_column(default=1920)
    bitrate_kbps: Mapped[int] = mapped_column(default=8000)
    caption_style: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    safe_zone_margins: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_default: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)


class Clip(Base):
    __tablename__ = "clips"
    id: Mapped[uuid.UUID] = _uuid_col()
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clip_candidates.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(Text)
    start_seconds: Mapped[float] = mapped_column(Numeric)
    end_seconds: Mapped[float] = mapped_column(Numeric)
    crop_box: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    face_track_enabled: Mapped[bool] = mapped_column(default=True)
    captions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    caption_style: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    hook_text: Mapped[list | None] = mapped_column(JSON, nullable=True)
    audio_settings: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    render_status: Mapped[str] = mapped_column(
        Enum("pending", "running", "succeeded", "failed", name="job_status"), default="pending"
    )
    rendered_object_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    rendered_preview_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    preset_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("presets.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="clips")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
