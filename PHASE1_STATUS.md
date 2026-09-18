# Phase 1 status

What's real vs. stubbed, so you know where to dig in first.

## End-to-end and wired
- **Ingest**: paste YouTube URL → instant oEmbed title/thumbnail preview →
  project created → single chained worker job (download → transcribe →
  AI highlight detection) → job-status polling in the UI.
- **File upload**: multipart upload straight to S3/MinIO from the API,
  same downstream pipeline as URL ingest.
- **Transcription**: faster-whisper, word-level timestamps, self-hosted.
- **AI clip suggestions**: calls the Claude Messages API with the transcript,
  asks for ranked candidate clips as JSON. Falls back to naive fixed-length
  windows if `LLM_API_KEY` isn't set, so the pipeline never dead-ends.
- **Clip review list**: candidates shown with title/rationale/timestamps,
  "Edit this clip" creates a `Clip` row and opens the editor.
- **Editor**: trim (numeric handles), face-track toggle + manual crop
  override, word-level caption editor, hook-text overlay tool, audio panel
  (noise reduction + loudness slider), preset picker — all persist to the
  `Clip` row via PATCH as you edit.
- **Render pipeline**: real ffmpeg command construction — trim, time-varying
  crop filter built from the face-tracking keyframes (or a static manual
  crop), `.ass` caption burn-in, `drawtext` hook overlays, `loudnorm` +
  optional `afftdn` audio processing, encode to the selected preset's
  resolution/bitrate. Uploads the result to S3 and the editor polls for
  the rendered preview + download link.
- **Presets**: CRUD endpoints; three sensible defaults (YouTube Shorts,
  TikTok, Instagram Reels) auto-seeded on first request.

## Stubbed / needs your attention before this is production-ready
- **Face tracking accuracy**: MediaPipe's single-frame face detector with a
  moving-average smoother is a reasonable v1, but has no identity tracking
  across cuts (if the camera cuts to a different speaker mid-clip, the crop
  will jump to whoever's face is largest in that frame, not necessarily the
  "main" speaker). A proper implementation would add face re-identification
  or let the user pin a face.
- **Waveform view**: `Timeline` component has a placeholder track, not real
  audio waveform data — wire up wavesurfer.js or similar against the source
  audio.
- **Video playback in the editor**: the editor doesn't currently render the
  actual source video (no signed playback URL endpoint yet), so the crop-box
  and caption editors are "blind" — you're editing numbers, not seeing them
  overlaid on the video. Add a `GET /projects/{id}/playback-url` endpoint
  (signed S3 URL) and an actual `<video>` element with an overlay canvas for
  the crop box.
- **Draggable crop box / timeline handles**: currently numeric inputs, not
  drag-on-video. Needs the video element above first.
- **`Job` progress polling granularity**: only 4 checkpoints (10/40/75/100%).
  Fine for now; wire finer-grained progress if downloads/transcription are
  slow enough to bother users.
- **Auth**: none. Every endpoint is open. Add auth before deploying anywhere
  reachable from the internet.
- **Cost/rate limiting**: no guardrails on video length, LLM spend, or
  concurrent jobs per user.

## Not started (by design — see BUILD PRIORITY in the original spec)
- Phase 2: OAuth + one-click publish to YouTube/TikTok/Instagram, post-history
  dashboard with analytics. `publish_history` table and `routers/publish.py`
  are the intended integration points.
- Phase 3: virality scoring, auto B-roll/emoji insertion, team collaboration,
  scheduling.
