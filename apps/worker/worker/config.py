import os
from dataclasses import dataclass


@dataclass
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "postgresql://clipforge:clipforge@postgres:5432/clipforge")
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

    s3_endpoint_url: str = os.getenv("S3_ENDPOINT_URL", "http://minio:9000")
    s3_access_key: str = os.getenv("S3_ACCESS_KEY", "minioadmin")
    s3_secret_key: str = os.getenv("S3_SECRET_KEY", "minioadmin")
    s3_bucket_source: str = os.getenv("S3_BUCKET_SOURCE", "clipforge-source")
    s3_bucket_rendered: str = os.getenv("S3_BUCKET_RENDERED", "clipforge-rendered")
    s3_region: str = os.getenv("S3_REGION", "auto")
    s3_public_base_url: str = os.getenv("S3_PUBLIC_BASE_URL", "http://localhost:9000")

    ingest_backend: str = os.getenv("INGEST_BACKEND", "self_hosted")
    managed_ingest_api_key: str = os.getenv("MANAGED_INGEST_API_KEY", "")

    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "claude-sonnet-4-6")

    whisper_model_size: str = os.getenv("WHISPER_MODEL_SIZE", "small")
    whisper_device: str = os.getenv("WHISPER_DEVICE", "cpu")

    media_scratch_dir: str = os.getenv("MEDIA_SCRATCH_DIR", "/tmp/clipforge")


settings = Settings()
os.makedirs(settings.media_scratch_dir, exist_ok=True)
