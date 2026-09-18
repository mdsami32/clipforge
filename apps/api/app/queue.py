from redis import Redis
from rq import Queue

from .config import settings

redis_conn = Redis.from_url(settings.redis_url)

# Separate queues so heavy CV/render work doesn't starve quick transcription jobs.
ingest_queue = Queue("clipforge:ingest", connection=redis_conn)
analyze_queue = Queue("clipforge:analyze", connection=redis_conn)
render_queue = Queue("clipforge:render", connection=redis_conn)
