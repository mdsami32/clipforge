# ClipForge

Self-hosted, transparent alternative to Opus Clip. Paste a YouTube URL or upload a
video, get AI-suggested vertical (9:16) clips with auto face-tracking, editable
captions, hook-text overlays, and platform export presets.

## Architecture

```
apps/
  web/      Next.js 14 (App Router) + TypeScript — dashboard, clip review, in-browser editor
  api/      FastAPI — REST endpoints, enqueues jobs, reads job/clip state from Postgres
  worker/   Python RQ workers — download (yt-dlp), transcribe (faster-whisper),
            AI highlight detection (LLM), face-track + vertical reframe (mediapipe/OpenCV),
            render (ffmpeg)
packages/
  shared-types/   TypeScript types shared by the web app (mirrors the API schemas)
infra/
  init.sql        Postgres schema
```

### Why this stack

- **FastAPI over Node for the API**: the heaviest logic (transcription, CV,
  ffmpeg orchestration) is Python-native, so keeping the API in Python avoids a
  cross-language boundary between "enqueue job" and "the code that processes it."
  The web app talks to the API purely over HTTP/JSON, so this is swappable for a
  Node/Express API later without touching the frontend.
- **RQ (Redis Queue) over BullMQ**: BullMQ is JS-only. Since workers are Python
  (ffmpeg/OpenCV/Whisper bindings are far more mature there), RQ keeps producer
  and consumer in one language. Redis is still the broker, so this is a drop-in
  swap for BullMQ if you later move workers to Node.
- **Postgres**: relational data (projects → clips → transcripts → presets →
  publish history) with clear foreign keys; also gives you real transactions for
  job-status updates.
- **S3-compatible storage (R2/MinIO locally)**: source videos and rendered
  clips never touch Postgres; only their object keys do.
- **Swappable ingest backend**: `INGEST_BACKEND=self_hosted` uses yt-dlp +
  faster-whisper in the worker. `INGEST_BACKEND=managed` calls out to a hosted
  API (Apify/Supadata) via `worker/tasks/managed_ingest.py`. Swap with one env var.

## Local dev

```bash
cp .env.example .env
docker-compose up --build
```

- Web: http://localhost:3000
- API: http://localhost:8000/docs (FastAPI auto-generated Swagger UI)
- Postgres: localhost:5432
- Redis: localhost:6379
- MinIO (S3-compatible, local only): http://localhost:9001 (console)

## Status

Phase 1 (MVP) scaffold: ingest → oEmbed preview → download+transcribe worker →
AI clip suggestions → manual timeline trim → vertical reframe + face tracking →
caption generation/editing → hook text overlays → audio normalization → export
presets → download. See `PHASE1_STATUS.md` for what's wired up end-to-end vs.
stubbed with clear TODOs.

Phase 2 (OAuth + one-click publish + analytics dashboard) and Phase 3
(virality scoring, auto B-roll, collaboration, scheduling) are not started —
the DB schema and API already leave room for them (see `publish_history` table
and `routers/publish.py` stub).
