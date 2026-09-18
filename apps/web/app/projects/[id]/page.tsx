"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, ClipCandidate, Job, Project } from "@/lib/api";

export default function ProjectPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [candidates, setCandidates] = useState<ClipCandidate[]>([]);
  const [creatingId, setCreatingId] = useState<string | null>(null);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 3000);
    return () => clearInterval(interval);
  }, [id]);

  async function refresh() {
    const p = await api.getProject(id);
    setProject(p);
    setJobs(await api.listJobs(id));
    if (p.status === "succeeded") {
      setCandidates(await api.listCandidates(id));
    }
  }

  async function pickCandidate(candidateId: string) {
    setCreatingId(candidateId);
    try {
      const clip = await api.createClipFromCandidate(id, candidateId);
      router.push(`/projects/${id}/clips/${clip.id}`);
    } finally {
      setCreatingId(null);
    }
  }

  if (!project) return <p>Loading…</p>;

  const activeJob = jobs.find((j) => j.status === "running" || j.status === "pending");

  return (
    <div>
      <h1>{project.title}</h1>

      {project.status !== "succeeded" && (
        <div className="card">
          <p>
            Status: <strong>{project.status}</strong>
          </p>
          {activeJob && (
            <div>
              <div style={{ background: "#eee", borderRadius: 8, overflow: "hidden", height: 8 }}>
                <div
                  style={{
                    width: `${activeJob.progress}%`,
                    background: "#111",
                    height: "100%",
                    transition: "width 0.3s",
                  }}
                />
              </div>
              <p style={{ fontSize: 13, color: "#666" }}>
                {activeJob.job_type} — {activeJob.progress}%
              </p>
            </div>
          )}
          {project.status === "failed" && <p style={{ color: "#c00" }}>{project.error_message}</p>}
        </div>
      )}

      {project.status === "succeeded" && (
        <>
          <h2>Suggested clips</h2>
          {candidates.length === 0 && <p style={{ color: "#666" }}>No candidates found.</p>}
          {candidates
            .slice()
            .sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
            .map((c) => (
              <div key={c.id} className="card">
                <strong>{c.title}</strong>
                <p style={{ color: "#555", fontSize: 14 }}>{c.rationale}</p>
                <p style={{ fontSize: 13, color: "#888" }}>
                  {formatTime(c.start_seconds)} – {formatTime(c.end_seconds)}
                  {c.score != null && ` · score ${Math.round(c.score)}`}
                </p>
                <button className="primary" disabled={creatingId === c.id} onClick={() => pickCandidate(c.id)}>
                  {creatingId === c.id ? "Opening editor…" : "Edit this clip"}
                </button>
              </div>
            ))}
        </>
      )}
    </div>
  );
}

function formatTime(seconds: number) {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}
