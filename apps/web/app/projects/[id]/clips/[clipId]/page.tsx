"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, Clip, Preset } from "@/lib/api";
import { Timeline } from "@/components/Timeline";
import { CaptionEditor, CaptionWord } from "@/components/CaptionEditor";
import { HookTextEditor, HookOverlay } from "@/components/HookTextEditor";
import { CropBoxEditor } from "@/components/CropBoxEditor";
import { AudioPanel } from "@/components/AudioPanel";
import { PresetPicker } from "@/components/PresetPicker";

export default function ClipEditorPage() {
  const { clipId } = useParams<{ clipId: string }>();
  const [clip, setClip] = useState<Clip | null>(null);
  const [presets, setPresets] = useState<Preset[]>([]);
  const [saving, setSaving] = useState(false);
  const [rendering, setRendering] = useState(false);

  useEffect(() => {
    api.getClip(clipId).then(setClip);
    api.listPresets().then((ps) => {
      setPresets(ps);
      setClip((c) => (c && !c.preset_id ? { ...c, preset_id: ps.find((p) => p.is_default)?.id ?? null } : c));
    });
  }, [clipId]);

  // Poll while a render is in flight.
  useEffect(() => {
    if (!clip || clip.render_status !== "running") return;
    const interval = setInterval(async () => {
      const updated = await api.getClip(clipId);
      setClip(updated);
      if (updated.render_status !== "running") setRendering(false);
    }, 3000);
    return () => clearInterval(interval);
  }, [clip?.render_status, clipId]);

  async function save(patch: Partial<Clip>) {
    if (!clip) return;
    const next = { ...clip, ...patch };
    setClip(next);
    setSaving(true);
    try {
      await api.updateClip(clip.id, patch);
    } finally {
      setSaving(false);
    }
  }

  async function handleRender() {
    if (!clip) return;
    setRendering(true);
    const updated = await api.renderClip(clip.id);
    setClip(updated);
  }

  if (!clip) return <p>Loading…</p>;

  const clipDuration = clip.end_seconds - clip.start_seconds;
  // NOTE: assumes the source video is at least this long past `start_seconds`;
  // a real duration bound should come from `project.duration_seconds`.
  const timelineDuration = clip.end_seconds + Math.max(30, clipDuration);

  return (
    <div>
      <h1>{clip.title}</h1>
      <input
        type="text"
        value={clip.title}
        onChange={(e) => save({ title: e.target.value })}
        style={{ marginBottom: 16 }}
      />

      <section className="card">
        <h3>Trim</h3>
        <Timeline
          durationSeconds={timelineDuration}
          start={clip.start_seconds}
          end={clip.end_seconds}
          onChange={(start, end) => save({ start_seconds: start, end_seconds: end })}
        />
      </section>

      <section className="card">
        <h3>Vertical reframe</h3>
        <CropBoxEditor
          faceTrackEnabled={clip.face_track_enabled}
          cropBox={clip.crop_box ?? null}
          onChange={(faceTrackEnabled, cropBox) => save({ face_track_enabled: faceTrackEnabled, crop_box: cropBox })}
        />
      </section>

      <section className="card">
        <h3>Captions</h3>
        <CaptionEditor
          captions={(clip.captions as CaptionWord[]) ?? []}
          onChange={(captions) => save({ captions })}
        />
      </section>

      <section className="card">
        <h3>Hook / title text</h3>
        <HookTextEditor
          overlays={(clip.hook_text as HookOverlay[]) ?? []}
          onChange={(hook_text) => save({ hook_text })}
        />
      </section>

      <section className="card">
        <h3>Audio</h3>
        <AudioPanel settings={clip.audio_settings ?? {}} onChange={(audio_settings) => save({ audio_settings })} />
      </section>

      <section className="card">
        <h3>Export preset</h3>
        <PresetPicker
          presets={presets}
          selectedId={clip.preset_id ?? null}
          onSelect={(preset_id) => save({ preset_id })}
        />
      </section>

      <section className="card">
        <h3>Export</h3>
        <button className="primary" disabled={rendering} onClick={handleRender}>
          {rendering || clip.render_status === "running" ? "Rendering…" : "Render clip"}
        </button>
        {saving && <span style={{ marginLeft: 12, fontSize: 13, color: "#888" }}>Saving…</span>}
        {clip.render_status === "succeeded" && clip.rendered_preview_url && (
          <div style={{ marginTop: 16 }}>
            <video src={clip.rendered_preview_url} controls style={{ maxWidth: 280, borderRadius: 12 }} />
            <div style={{ marginTop: 8 }}>
              <a href={clip.rendered_preview_url} download>
                <button>Download</button>
              </a>
            </div>
          </div>
        )}
        {clip.render_status === "failed" && <p style={{ color: "#c00" }}>Render failed — check the worker logs.</p>}
      </section>
    </div>
  );
}
