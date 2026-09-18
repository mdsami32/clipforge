"""RQ worker entrypoint. Listens on all three queues so a single worker
container can process the whole pipeline in dev; scale by running multiple
`worker` replicas (and split queues across dedicated containers) in prod —
render jobs are the most CPU/GPU-heavy and benefit most from their own pool.
"""
from redis import Redis
from rq import Worker

from .config import settings

listen = ["clipforge:ingest", "clipforge:analyze", "clipforge:render"]

if __name__ == "__main__":
    conn = Redis.from_url(settings.redis_url)
    worker = Worker(listen, connection=conn)
    worker.work()
