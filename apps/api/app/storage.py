import boto3

from .config import settings

s3_client = boto3.client(
    "s3",
    endpoint_url=settings.s3_endpoint_url,
    aws_access_key_id=settings.s3_access_key,
    aws_secret_access_key=settings.s3_secret_key,
    region_name=settings.s3_region,
)


def public_url(bucket: str, key: str) -> str:
    return f"{settings.s3_public_base_url}/{bucket}/{key}"


def ensure_buckets():
    for bucket in (settings.s3_bucket_source, settings.s3_bucket_rendered):
        try:
            s3_client.head_bucket(Bucket=bucket)
        except Exception:
            s3_client.create_bucket(Bucket=bucket)
