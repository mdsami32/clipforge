from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    env: str = "development"
    secret_key: str = "change-me"

    database_url: str = "postgresql://clipforge:clipforge@postgres:5432/clipforge"
    redis_url: str = "redis://redis:6379/0"

    s3_endpoint_url: str = "http://minio:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_source: str = "clipforge-source"
    s3_bucket_rendered: str = "clipforge-rendered"
    s3_region: str = "auto"
    s3_public_base_url: str = "http://localhost:9000"

    ingest_backend: str = "self_hosted"  # "self_hosted" | "managed"
    managed_ingest_api_key: str | None = None

    llm_api_key: str | None = None
    llm_model: str = "claude-sonnet-4-6"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
