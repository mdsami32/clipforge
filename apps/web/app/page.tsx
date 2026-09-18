"use client";

import { useEffect, useState } from "react";
import { api, Project } from "@/lib/api";

export default function DashboardPage() {
  const [url, setUrl] = useState("");
  const [preview, setPreview] = useState<{ title: string; thumbnail_url: string } | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);

  useEffect(() => {
    refreshProjects();
    const interval = setInterval(refreshProjects, 4000);
    return () => clearInterval(interval);
  }, []);

  function refreshProjects() {
    api.listProjects().then(setProjects).catch(() => {});
  }

  // Debounced instant oEmbed preview as soon as a plausible YouTube URL is pasted.
  useEffect(() => {
    if (!/youtu\.?be/.test(url)) {
      setPreview(null);
      return;
    }
    const handle = setTimeout(() => {
      api
        .oembedPreview(url)
        .then((p) => {
          setPreview(p);
          setPreviewError(null);
        })
        .catch(() => setPreviewError("Couldn't fetch a preview for that URL."));
    }, 400);
    return () => clearTimeout(handle);
  }, [url]);

  async function handleSubmitUrl() {
    setSubmitting(true);
    try {
      await api.createProjectFromUrl(url);
      setUrl("");
      setPreview(null);
      refreshProjects();
    } finally {
      setSubmitting(false);
    }
  }

  async function handleUpload(file: File) {
    setSubmitting(true);
    try {
      await api.uploadProject(file);
      refreshProjects();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <h1>New project</h1>
      <div className="card">
        <p style={{ marginTop: 0, color: "#666" }}>Paste a YouTube URL, or upload a video file.</p>
        <input
          type="url"
          placeholder="https://www.youtube.com/watch?v=..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        {previewError && <p style={{ color: "#c00", fontSize: 13 }}>{previewError}</p>}
        {preview && (
          <div style={{ display: "flex", gap: 12, marginTop: 12, alignItems: "center" }}>
            <img src={preview.thumbnail_url} alt="" width={120} style={{ borderRadius: 8 }} />
            <strong>{preview.title}</strong>
          </div>
        )}
        <div style={{ marginTop: 12, display: "flex", gap: 12 }}>
          <button className="primary" disabled={!url || submitting} onClick={handleSubmitUrl}>
            {submitting ? "Starting…" : "Start processing"}
          </button>
          <label style={{ alignSelf: "center", cursor: "pointer", color: "#555" }}>
            or{" "}
            <input
              type="file"
              accept="video/*"
              style={{ display: "none" }}
              onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])}
            />
            <span style={{ textDecoration: "underline" }}>upload a file</span>
          </label>
        </div>
      </div>

      <h1>Projects</h1>
      {projects.length === 0 && <p style={{ color: "#666" }}>No projects yet.</p>}
      {projects.map((p) => (
        <a key={p.id} href={`/projects/${p.id}`} style={{ textDecoration: "none", color: "inherit" }}>
          <div className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <strong>{p.title}</strong>
              <div style={{ fontSize: 13, color: "#666" }}>{p.status}</div>
            </div>
            {p.thumbnail_url && <img src={p.thumbnail_url} width={80} style={{ borderRadius: 6 }} />}
          </div>
        </a>
      ))}
    </div>
  );
}
