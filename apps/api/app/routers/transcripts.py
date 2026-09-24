import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import db, schemas

router = APIRouter(tags=["transcripts"])


@router.get("/projects/{project_id}/transcript", response_model=schemas.TranscriptOut)
def get_project_transcript(project_id: uuid.UUID, session: Session = Depends(db.get_db)):
    transcript = (
        session.query(db.Transcript)
        .filter(db.Transcript.project_id == project_id)
        .order_by(db.Transcript.created_at.desc())
        .first()
    )
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return transcript
