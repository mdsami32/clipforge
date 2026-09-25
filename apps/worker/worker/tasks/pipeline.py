"""Orchestrates the full ingest pipeline for a project:
download -> transcribe -> AI highlight detection -> persist clip_candidates.

Enqueued as a single RQ job so job-status polling only has to watch one
`jobs` row; each stage still updates `progress` so the UI can show granular
status ("Downloading…" / "Transcribing…" / "Finding highlights…").
"""
import os
import uuid

from .. import db
from ..config import settings
from ..storage import upload_from_path
from . import download as download_task
from . import managed_ingest
from ..candidates.generate import generate_clip_candidates
from ..transcription.normalize import normalize_word_list
from .transcribe import transcribe_timeline


def run_ingest_pipeline(project_id: str, job_id: str):
    session = db.get_session()
    try:
        project = session.get(db.Project, uuid.UUID(project_id))
        job = session.get(db.Job, uuid.UUID(job_id))
        if not project or not job:
            return

        project.status = "running"
        job.status = "running"
        session.commit()

        work_dir = os.path.join(settings.media_scratch_dir, project_id)
        os.makedirs(work_dir, exist_ok=True)

        # --- Stage 1: download ---
        _set_progress(session, job, 10)
        if project.source_type == "youtube_url":
            if settings.ingest_backend == "managed":
                local_path = managed_ingest.download(project.source_url)
            else:
                local_path, info = download_task.download_youtube_video(project.source_url, work_dir)
                project.title = info.get("title", project.title)
                project.duration_seconds = info.get("duration")
                project.thumbnail_url = info.get("thumbnail")

            object_key = f"{project.id}/source.mp4"
            upload_from_path(settings.s3_bucket_source, object_key, local_path)
            project.source_object_key = object_key
        else:
            # Already uploaded directly to S3 in the API layer; just pull it
            # down locally for transcription.
            from ..storage import download_to_path

            local_path = os.path.join(work_dir, "source.mp4")
            download_to_path(settings.s3_bucket_source, project.source_object_key, local_path)

        session.commit()

        # --- Stage 2: transcribe ---
        _set_progress(session, job, 40)
        if settings.ingest_backend == "managed":
            words, language = managed_ingest.transcribe(local_path)
            transcript = normalize_word_list(words, language=language, duration=project.duration_seconds)
        else:
            transcript = transcribe_timeline(local_path)

        session.add(
            db.Transcript(
                project_id=project.id,
                transcript=transcript,
                words=transcript["words"],
                language=transcript["language"],
            )
        )
        if not project.duration_seconds and transcript["duration"]:
            project.duration_seconds = transcript["duration"]
        session.commit()

        # --- Stage 3: deterministic candidate generation ---
        _set_progress(session, job, 75)
        candidates = generate_clip_candidates(transcript)
        for c in candidates:
            session.add(
                db.ClipCandidate(
                    project_id=project.id,
                    title=c["title"],
                    rationale=c["rationale"],
                    start_seconds=c["start_seconds"],
                    end_seconds=c["end_seconds"],
                    score=c.get("score"),
                )
            )
        session.commit()

        _set_progress(session, job, 100)
        job.status = "succeeded"
        project.status = "succeeded"
        session.commit()

    except Exception as e:  # noqa: BLE001
        session.rollback()
        job = session.get(db.Job, uuid.UUID(job_id))
        project = session.get(db.Project, uuid.UUID(project_id))
        if job:
            job.status = "failed"
            job.error_message = str(e)
        if project:
            project.status = "failed"
            project.error_message = str(e)
        session.commit()
        raise e
    finally:
        session.close()


def _set_progress(session, job, progress: int):
    job.progress = progress
    session.commit()
