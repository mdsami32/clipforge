import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import db, schemas

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/by-project/{project_id}", response_model=list[schemas.JobOut])
def list_jobs_for_project(project_id: uuid.UUID, session: Session = Depends(db.get_db)):
    jobs = (
        session.query(db.Job)
        .filter(db.Job.project_id == project_id)
        .order_by(db.Job.created_at.asc())
        .all()
    )
    return jobs


@router.get("/{job_id}", response_model=schemas.JobOut)
def get_job(job_id: uuid.UUID, session: Session = Depends(db.get_db)):
    job = session.get(db.Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
