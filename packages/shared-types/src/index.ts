export * from "./transcript";

// Mirrors apps/api/app/schemas.py. Kept here so the frontend and any future
// Node service share one source of truth for the wire format — apps/web
// currently redeclares these in lib/api.ts for zero-build-step simplicity,
// but should import from here once the web app has its own build pipeline
// wired to this package.

export type JobStatus = "pending" | "running" | "succeeded" | "failed";
export type IngestSource = "youtube_url" | "upload";
export type PublishPlatform = "youtube" | "tiktok" | "instagram";

export interface Project {
  id: string;
  title: string;
  source_type: IngestSource;
  source_url?: string;
  thumbnail_url?: string;
  duration_seconds?: number;
  status: JobStatus;
  error_message?: string;
}

export interface ClipCandidate {
  id: string;
  title: string;
  rationale: string;
  start_seconds: number;
  end_seconds: number;
  score?: number;
  thumbnail_url?: string;
}

export interface Clip {
  id: string;
  project_id: string;
  title: string;
  start_seconds: number;
  end_seconds: number;
  crop_box?: { x: number; y: number; w: number; h: number } | null;
  face_track_enabled: boolean;
  captions?: { word: string; start: number; end: number }[] | null;
  caption_style?: Record<string, unknown> | null;
  hook_text?: Record<string, unknown>[] | null;
  audio_settings?: { noise_reduction?: boolean; loudness_target_lufs?: number } | null;
  render_status: JobStatus;
  rendered_preview_url?: string | null;
  preset_id?: string | null;
}

export interface Preset {
  id: string;
  name: string;
  platform?: PublishPlatform | null;
  resolution_w: number;
  resolution_h: number;
  bitrate_kbps: number;
  caption_style?: Record<string, unknown> | null;
  safe_zone_margins?: Record<string, number> | null;
  is_default: boolean;
}
