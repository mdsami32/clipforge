from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from . import db
from .routers import clips, ingest, jobs, oembed, presets, publish, transcripts
from .storage import ensure_buckets

app = FastAPI(title="ClipForge API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(oembed.router)
app.include_router(ingest.router)
app.include_router(jobs.router)
app.include_router(clips.router)
app.include_router(transcripts.router)
app.include_router(presets.router)
app.include_router(publish.router)


@app.on_event("startup")
def on_startup():
    db.Base.metadata.create_all(bind=db.engine)
    with db.engine.begin() as connection:
        connection.execute(text("ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS transcript JSONB NOT NULL DEFAULT '{}'::jsonb"))
    ensure_buckets()


@app.get("/health")
def health():
    return {"status": "ok"}
