"""Final render pipeline: trim -> vertical crop (face-tracked or manual) ->
burn captions -> burn hook text overlay -> audio normalize/denoise -> encode
to the clip's preset. Runs as a single ffmpeg invocation with a constructed
filter graph, driven by whatever the clip's current edit state is.
"""
import json
import os
import subprocess
import uuid

import cv2

from .. import db
from ..config import settings
from ..storage import download_to_path, public_url, upload_from_path
from .captions import write_ass_file
from .reframe import compute_face_track, crop_box_for_frame

DEFAULT_PRESET = {"resolution_w": 1080, "resolution_h": 1920, "bitrate_kbps": 8000, "safe_zone_margins": {}}


def run_render_pipeline(clip_id: str):
    session = db.get_session()
    try:
        clip = session.get(db.Clip, uuid.UUID(clip_id))
        if not clip:
            return
        project = session.get(db.Project, clip.project_id)
        preset = session.get(db.Preset, clip.preset_id) if clip.preset_id else None

        clip.render_status = "running"
        session.commit()

        work_dir = os.path.join(settings.media_scratch_dir, str(clip.id))
        os.makedirs(work_dir, exist_ok=True)

        source_local = os.path.join(work_dir, "source.mp4")
        download_to_path(settings.s3_bucket_source, project.source_object_key, source_local)

        out_local = os.path.join(work_dir, "clip.mp4")
        _render_clip(
            source_path=source_local,
            out_path=out_local,
            work_dir=work_dir,
            clip=clip,
            preset=preset,
        )

        object_key = f"{clip.project_id}/{clip.id}/rendered.mp4"
        upload_from_path(settings.s3_bucket_rendered, object_key, out_local)

        clip.rendered_object_key = object_key
        clip.rendered_preview_url = public_url(settings.s3_bucket_rendered, object_key)
        clip.render_status = "succeeded"
        session.commit()
    except Exception as e:  # noqa: BLE001 — surface any failure onto the clip row
        session.rollback()
        clip = session.get(db.Clip, uuid.UUID(clip_id))
        if clip:
            clip.render_status = "failed"
            session.commit()
        raise e
    finally:
        session.close()


def _render_clip(source_path: str, out_path: str, work_dir: str, clip, preset):
    resolution_w = preset.resolution_w if preset else DEFAULT_PRESET["resolution_w"]
    resolution_h = preset.resolution_h if preset else DEFAULT_PRESET["resolution_h"]
    bitrate_kbps = preset.bitrate_kbps if preset else DEFAULT_PRESET["bitrate_kbps"]

    cap = cv2.VideoCapture(source_path)
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    crop_expr = _build_crop_filter(source_path, clip, frame_w, frame_h)

    filters = [
        f"trim=start={clip.start_seconds}:end={clip.end_seconds}",
        "setpts=PTS-STARTPTS",
        crop_expr,
        f"scale={resolution_w}:{resolution_h}",
    ]

    if clip.captions:
        ass_path = os.path.join(work_dir, "captions.ass")
        write_ass_file(clip.captions, clip.caption_style, ass_path, resolution_w, resolution_h)
        filters.append(f"subtitles={ass_path}")

    for overlay in clip.hook_text or []:
        filters.append(_drawtext_filter(overlay, resolution_w, resolution_h))

    video_filter = ",".join(filters)

    audio_filters = []
    audio_settings = clip.audio_settings or {}
    if audio_settings.get("noise_reduction"):
        audio_filters.append("afftdn")
    loudness_target = audio_settings.get("loudness_target_lufs", -14)
    audio_filters.append(f"loudnorm=I={loudness_target}:TP=-1.5:LRA=11")
    audio_filter = ",".join(audio_filters)

    cmd = [
        "ffmpeg", "-y",
        "-i", source_path,
        "-vf", video_filter,
        "-af", audio_filter,
        "-b:v", f"{bitrate_kbps}k",
        "-c:v", "libx264", "-preset", "medium",
        "-c:a", "aac", "-b:a", "192k",
        out_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def _build_crop_filter(source_path: str, clip, frame_w: int, frame_h: int) -> str:
    """Static manual crop_box if set; otherwise sample the face track and use
    a time-varying crop built as a chained ffmpeg `if()` expression over the
    tracked keyframes (keeps the speaker centered without re-encoding twice)."""
    if clip.crop_box:
        b = clip.crop_box
        return f"crop={b['w']}:{b['h']}:{b['x']}:{b['y']}"

    if not clip.face_track_enabled:
        return _center_crop_filter(frame_w, frame_h)

    track = compute_face_track(source_path, float(clip.start_seconds), float(clip.end_seconds))
    if not track:
        return _center_crop_filter(frame_w, frame_h)

    # Sample a handful of crop boxes across the clip and build a piecewise
    # x/y expression ffmpeg can evaluate per-frame via the `t` variable.
    sample_times = sorted({p["t"] - float(clip.start_seconds) for p in track})
    boxes = [
        crop_box_for_frame(track, p["t"], frame_w, frame_h) for p in track
    ]
    w, h = boxes[0]["w"], boxes[0]["h"]

    x_expr = _piecewise_expr(sample_times, [b["x"] for b in boxes])
    y_expr = _piecewise_expr(sample_times, [b["y"] for b in boxes])

    return f"crop={w}:{h}:'{x_expr}':'{y_expr}'"


def _center_crop_filter(frame_w: int, frame_h: int, target_aspect: float = 9 / 16) -> str:
    if frame_w / frame_h > target_aspect:
        crop_h = frame_h
        crop_w = int(crop_h * target_aspect)
    else:
        crop_w = frame_w
        crop_h = int(crop_w / target_aspect)
    x = (frame_w - crop_w) // 2
    y = (frame_h - crop_h) // 2
    return f"crop={crop_w}:{crop_h}:{x}:{y}"


def _piecewise_expr(times: list[float], values: list[float]) -> str:
    """Builds a nested if(between(t,t0,t1), lerp, ...) expression string for
    ffmpeg's eval. Falls back to the last value beyond the final keyframe."""
    if not times:
        return "0"
    expr = str(int(values[-1]))
    for i in range(len(times) - 1, 0, -1):
        t0, t1 = times[i - 1], times[i]
        v0, v1 = values[i - 1], values[i]
        # linear interpolation between keyframes
        lerp = f"({v0}+({v1}-{v0})*(t-{t0})/({t1}-{t0}+0.0001))"
        expr = f"if(between(t,{t0},{t1}),{lerp},{expr})"
    return expr


def _drawtext_filter(overlay: dict, video_w: int, video_h: int) -> str:
    text = overlay.get("text", "").replace(":", "\\:").replace("'", "\\'")
    font_size = overlay.get("font_size", 72)
    color = overlay.get("color", "white")
    position = overlay.get("position", "top")
    start = overlay.get("start", 0)
    end = overlay.get("end", 999999)

    y_expr = {"top": "h*0.1", "center": "(h-text_h)/2", "bottom": "h*0.8"}.get(position, "h*0.1")

    return (
        f"drawtext=text='{text}':fontsize={font_size}:fontcolor={color}"
        f":x=(w-text_w)/2:y={y_expr}"
        f":enable='between(t,{start},{end})'"
        f":box=1:boxcolor=black@0.4:boxborderw=10"
    )
