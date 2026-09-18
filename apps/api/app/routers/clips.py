import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import db, schemas
from ..queue import render_queue

router = APIRouter(tags=["clips"])


@router.get("/projects/{project_id}/candidates", response_model=list[schemas.ClipCandidateOut])
def list_candidates(project_id: uuid.UUID, session: Session = Depends(db.get_db)):
    return (
        session.query(db.ClipCandidate)
        .filter(db.ClipCandidate.project_id == project_id)
        .order_by(db.ClipCandidate.score.desc().nullslast())
        .all()
    )


@router.post("/projects/{project_id}/clips", response_model=schemas.ClipOut)
def create_clip_from_candidate(
    project_id: uuid.UUID, payload: schemas.ClipCreateFromCandidate, session: Session = Depends(db.get_db)
):
    candidate = session.get(db.ClipCandidate, payload.candidate_id)
    if not candidate or candidate.project_id != project_id:
        raise HTTPException(status_code=404, detail="Candidate not found")

    clip = db.Clip(
        project_id=project_id,
        candidate_id=candidate.id,
        title=candidate.title,
        start_seconds=candidate.start_seconds,
        end_seconds=candidate.end_seconds,
        face_track_enabled=True,
        audio_settings={"noise_reduction": False, "loudness_target_lufs": -14},
    )
    session.add(clip)
    session.commit()
    session.refresh(clip)
    return clip


@router.get("/projects/{project_id}/clips", response_model=list[schemas.ClipOut])
def list_clips(project_id: uuid.UUID, session: Session = Depends(db.get_db)):
    return session.query(db.Clip).filter(db.Clip.project_id == project_id).all()


@router.get("/clips/{clip_id}", response_model=schemas.ClipOut)
def get_clip(clip_id: uuid.UUID, session: Session = Depends(db.get_db)):
    clip = session.get(db.Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    return clip


@router.patch("/clips/{clip_id}", response_model=schemas.ClipOut)
def update_clip(clip_id: uuid.UUID, payload: schemas.ClipUpdate, session: Session = Depends(db.get_db)):
    clip = session.get(db.Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(clip, field, value)
    session.commit()
    session.refresh(clip)
    return clip


@router.post("/clips/{clip_id}/render", response_model=schemas.ClipOut)
def render_clip(clip_id: uuid.UUID, session: Session = Depends(db.get_db)):
    """Enqueue the ffmpeg render job: vertical reframe + face track + captions +
    hook text + audio processing, per the clip's current edits and preset."""
    clip = session.get(db.Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    clip.render_status = "pending"
    session.commit()

    render_queue.enqueue(
        "worker.tasks.render.run_render_pipeline",
        str(clip.id),
        job_timeout="30m",
    )
    return clip
