const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export type Project = {
  id: string;
  title: string;
  source_type: "youtube_url" | "upload";
  source_url?: string;
  thumbnail_url?: string;
  duration_seconds?: number;
  status: "pending" | "running" | "succeeded" | "failed";
  error_message?: string;
};

export type Job = {
  id: string;
  project_id: string;
  job_type: string;
  status: "pending" | "running" | "succeeded" | "failed";
  progress: number;
  error_message?: string;
};

export type ClipCandidate = {
  id: string;
  title: string;
  rationale: string;
  start_seconds: number;
  end_seconds: number;
  score?: number;
  thumbnail_url?: string;
};

export type Clip = {
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
  render_status: "pending" | "running" | "succeeded" | "failed";
  rendered_preview_url?: string | null;
  preset_id?: string | null;
};

export type Preset = {
  id: string;
  name: string;
  platform?: "youtube" | "tiktok" | "instagram" | null;
  resolution_w: number;
  resolution_h: number;
  bitrate_kbps: number;
  caption_style?: Record<string, unknown> | null;
  safe_zone_margins?: Record<string, number> | null;
  is_default: boolean;
};

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: options?.body instanceof FormData ? undefined : { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API ${path} failed: ${res.status} ${detail}`);
  }
  return res.json();
}

export const api = {
  oembedPreview: (url: string) => request<{ title: string; author_name: string; thumbnail_url: string }>(
    `/oembed/youtube?url=${encodeURIComponent(url)}`
  ),
  createProjectFromUrl: (youtube_url: string) =>
    request<Project>("/projects", { method: "POST", body: JSON.stringify({ youtube_url }) }),
  uploadProject: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<Project>("/projects/upload", { method: "POST", body: form });
  },
  listProjects: () => request<Project[]>("/projects"),
  getProject: (id: string) => request<Project>(`/projects/${id}`),
  listJobs: (projectId: string) => request<Job[]>(`/jobs/by-project/${projectId}`),
  listCandidates: (projectId: string) => request<ClipCandidate[]>(`/projects/${projectId}/candidates`),
  createClipFromCandidate: (projectId: string, candidateId: string) =>
    request<Clip>(`/projects/${projectId}/clips`, {
      method: "POST",
      body: JSON.stringify({ candidate_id: candidateId }),
    }),
  listClips: (projectId: string) => request<Clip[]>(`/projects/${projectId}/clips`),
  getClip: (clipId: string) => request<Clip>(`/clips/${clipId}`),
  updateClip: (clipId: string, patch: Partial<Clip>) =>
    request<Clip>(`/clips/${clipId}`, { method: "PATCH", body: JSON.stringify(patch) }),
  renderClip: (clipId: string) => request<Clip>(`/clips/${clipId}/render`, { method: "POST" }),
  listPresets: () => request<Preset[]>("/presets"),
  createPreset: (preset: Omit<Preset, "id">) =>
    request<Preset>("/presets", { method: "POST", body: JSON.stringify(preset) }),
};
