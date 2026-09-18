"""Auto vertical reframe with face tracking.

Uses MediaPipe's face detector to find the dominant face per sampled frame,
then produces a smoothed per-frame crop-box track for a 9:16 output. The
render step consumes this track (or a manual override crop_box from the
clip's `crop_box` field) and feeds it to ffmpeg as a `crop`+`scale` filter.
"""
import cv2
import mediapipe as mp
import numpy as np

mp_face_detection = mp.solutions.face_detection


def compute_face_track(
    video_path: str,
    start_seconds: float,
    end_seconds: float,
    target_aspect: float = 9 / 16,
    sample_fps: float = 2.0,
) -> list[dict]:
    """Returns a smoothed list of {t, cx, cy} — normalized (0-1) crop-box
    center per sampled timestamp, tracking the largest detected face and
    falling back to frame-center when no face is found."""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    step = max(1, int(fps / sample_fps))
    start_frame = int(start_seconds * fps)
    end_frame = int(end_seconds * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    track: list[dict] = []
    with mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5) as detector:
        frame_idx = start_frame
        while frame_idx < end_frame:
            ok, frame = cap.read()
            if not ok:
                break
            if (frame_idx - start_frame) % step == 0:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = detector.process(rgb)
                cx, cy = 0.5, 0.5
                if result.detections:
                    largest = max(
                        result.detections,
                        key=lambda d: d.location_data.relative_bounding_box.width
                        * d.location_data.relative_bounding_box.height,
                    )
                    box = largest.location_data.relative_bounding_box
                    cx = box.xmin + box.width / 2
                    cy = box.ymin + box.height / 2
                track.append({"t": frame_idx / fps, "cx": cx, "cy": cy})
            frame_idx += 1
    cap.release()

    return _smooth_track(track)


def _smooth_track(track: list[dict], window: int = 5) -> list[dict]:
    """Simple moving average so the crop doesn't jitter frame-to-frame."""
    if len(track) < window:
        return track
    cxs = np.array([p["cx"] for p in track])
    cys = np.array([p["cy"] for p in track])
    kernel = np.ones(window) / window
    smoothed_cx = np.convolve(cxs, kernel, mode="same")
    smoothed_cy = np.convolve(cys, kernel, mode="same")
    return [
        {"t": p["t"], "cx": float(smoothed_cx[i]), "cy": float(smoothed_cy[i])}
        for i, p in enumerate(track)
    ]


def crop_box_for_frame(
    track: list[dict], t: float, frame_w: int, frame_h: int, target_aspect: float = 9 / 16
) -> dict:
    """Nearest-timestamp lookup into the track, converted into a pixel crop
    box of the target aspect ratio, clamped to frame bounds."""
    if not track:
        cx, cy = 0.5, 0.5
    else:
        nearest = min(track, key=lambda p: abs(p["t"] - t))
        cx, cy = nearest["cx"], nearest["cy"]

    if frame_w / frame_h > target_aspect:
        crop_h = frame_h
        crop_w = int(crop_h * target_aspect)
    else:
        crop_w = frame_w
        crop_h = int(crop_w / target_aspect)

    x = int(cx * frame_w - crop_w / 2)
    y = int(cy * frame_h - crop_h / 2)
    x = max(0, min(x, frame_w - crop_w))
    y = max(0, min(y, frame_h - crop_h))

    return {"x": x, "y": y, "w": crop_w, "h": crop_h}
