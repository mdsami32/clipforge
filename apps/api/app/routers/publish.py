"""Phase 2 stub. Left unimplemented on purpose:

Wiring real OAuth (YouTube Data API, TikTok Content Posting API, Instagram
Graph API) needs registered developer apps + redirect URIs owned by whoever
deploys this, so it can't be scaffolded generically. The `publish_history`
table and this router are the intended integration points — implement:

  POST /publish/oauth/{platform}/start    -> redirect to platform OAuth
  GET  /publish/oauth/{platform}/callback -> exchange code, store token
  POST /clips/{clip_id}/publish           -> enqueue worker.tasks.publish
  GET  /publish/history                   -> read publish_history table
"""
from fastapi import APIRouter

router = APIRouter(prefix="/publish", tags=["publish (phase 2, not implemented)"])
