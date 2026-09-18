"""Project creation: either a pasted YouTube URL or an uploaded file.

Both paths create a `Project` row and enqueue the ingest pipeline
(download -> transcribe -> analyze) as a single chained worker job. Job
progress is polled via GET /jobs/{project_id}.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import db, schemas
from ..config import settings
from ..queue import ingest_queue
from ..storage import public_url, s3_client

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=schemas.ProjectOut)
def create_project_from_youtube_url(
    payload: schemas.ProjectCreateFromURL, session: Session = Depends(db.get_db)
):
    project = db.Project(
        title=payload.youtube_url,  # replaced once oEmbed/transcode metadata lands
        source_type="youtube_url",
        source_url=payload.youtube_url,
        status="pending",
    )
    session.add(project)
    session.commit()
    session.refresh(project)

    job = db.Job(project_id=project.id, job_type="download", status="pending")
    session.add(job)
    session.commit()
    session.refresh(job)

    rq_job = ingest_queue.enqueue(
        "worker.tasks.pipeline.run_ingest_pipeline",
        str(project.id),
        str(job.id),
        job_timeout="30m",
    )
    job.rq_job_id = rq_job.id
    session.commit()

    return project


@router.post("/upload", response_model=schemas.ProjectOut)
def create_project_from_upload(file: UploadFile, session: Session = Depends(db.get_db)):
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a video")

    project = db.Project(title=file.filename or "Untitled upload", source_type="upload", status="pending")
    session.add(project)
    session.commit()
    session.refresh(project)

    object_key = f"{project.id}/source{_ext(file.filename)}"
    s3_client.upload_fileobj(file.file, settings.s3_bucket_source, object_key)
    project.source_object_key = object_key
    session.commit()

    job = db.Job(project_id=project.id, job_type="transcribe", status="pending")
    session.add(job)
    session.commit()
    session.refresh(job)

    rq_job = ingest_queue.enqueue(
        "worker.tasks.pipeline.run_ingest_pipeline",
        str(project.id),
        str(job.id),
        job_timeout="30m",
    )
    job.rq_job_id = rq_job.id
    session.commit()

    return project


@router.get("/{project_id}", response_model=schemas.ProjectOut)
def get_project(project_id: uuid.UUID, session: Session = Depends(db.get_db)):
    project = session.get(db.Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("", response_model=list[schemas.ProjectOut])
def list_projects(session: Session = Depends(db.get_db)):
    return session.query(db.Project).order_by(db.Project.created_at.desc()).all()


def _ext(filename: str | None) -> str:
    if not filename or "." not in filename:
        return ".mp4"
    return "." + filename.rsplit(".", 1)[-1]
