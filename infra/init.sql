-- ClipForge Postgres schema (Phase 1 + Phase 2 tables; Phase 2 tables unused until OAuth lands)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TYPE job_status AS ENUM ('pending', 'running', 'succeeded', 'failed');
CREATE TYPE ingest_source AS ENUM ('youtube_url', 'upload');
CREATE TYPE publish_status AS ENUM ('scheduled', 'pending', 'success', 'failed');
CREATE TYPE publish_platform AS ENUM ('youtube', 'tiktok', 'instagram');

CREATE TABLE projects (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title           TEXT NOT NULL,
    source_type     ingest_source NOT NULL,
    source_url      TEXT,                       -- YouTube URL, if applicable
    source_object_key TEXT,                     -- S3 key of uploaded/downloaded source video
    thumbnail_url   TEXT,
    duration_seconds NUMERIC,
    status          job_status NOT NULL DEFAULT 'pending',
    error_message   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE jobs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    job_type        TEXT NOT NULL,               -- download | transcribe | analyze | render
    status          job_status NOT NULL DEFAULT 'pending',
    progress        SMALLINT NOT NULL DEFAULT 0,  -- 0-100
    rq_job_id       TEXT,
    error_message   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE transcripts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    transcript      JSONB NOT NULL DEFAULT '{}'::jsonb, -- canonical normalized timeline
    -- legacy flattened word-level timestamps
    words           JSONB NOT NULL,
    language        TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE clip_candidates (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    rationale       TEXT NOT NULL,               -- "why this works"
    start_seconds   NUMERIC NOT NULL,
    end_seconds     NUMERIC NOT NULL,
    score           NUMERIC,                     -- optional ranking score from the LLM
    thumbnail_url   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE presets (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,
    platform        publish_platform,            -- null = custom/generic preset
    resolution_w    INTEGER NOT NULL DEFAULT 1080,
    resolution_h    INTEGER NOT NULL DEFAULT 1920,
    bitrate_kbps    INTEGER NOT NULL DEFAULT 8000,
    caption_style   JSONB,
    safe_zone_margins JSONB,                     -- {top, bottom, left, right} in px
    is_default      BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE clips (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id          UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    candidate_id        UUID REFERENCES clip_candidates(id) ON DELETE SET NULL,
    title               TEXT NOT NULL,
    start_seconds       NUMERIC NOT NULL,
    end_seconds         NUMERIC NOT NULL,
    crop_box            JSONB,                   -- manual override: {x, y, w, h} normalized 0-1, per keyframe or static
    face_track_enabled  BOOLEAN NOT NULL DEFAULT true,
    captions            JSONB,                   -- editable word-level captions: [{word, start, end}]
    caption_style       JSONB,                   -- font, size, color, position, animation
    hook_text           JSONB,                   -- [{text, start, end, position, font, animation}]
    audio_settings      JSONB,                   -- {noise_reduction: bool, loudness_target_lufs: number}
    render_status       job_status NOT NULL DEFAULT 'pending',
    rendered_object_key TEXT,
    rendered_preview_url TEXT,
    preset_id           UUID REFERENCES presets(id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Phase 2: publish history (unused until OAuth is implemented)
CREATE TABLE publish_history (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clip_id         UUID NOT NULL REFERENCES clips(id) ON DELETE CASCADE,
    platform        publish_platform NOT NULL,
    status          publish_status NOT NULL DEFAULT 'pending',
    scheduled_for   TIMESTAMPTZ,
    published_at    TIMESTAMPTZ,
    platform_post_id TEXT,
    platform_url    TEXT,
    views           BIGINT,
    likes           BIGINT,
    error_message   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_jobs_project_id ON jobs(project_id);
CREATE INDEX idx_clips_project_id ON clips(project_id);
CREATE INDEX idx_clip_candidates_project_id ON clip_candidates(project_id);
CREATE INDEX idx_transcripts_project_id_created_at ON transcripts(project_id, created_at DESC);
CREATE INDEX idx_publish_history_clip_id ON publish_history(clip_id);
