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


def download_to_path(bucket: str, key: str, local_path: str):
    s3_client.download_file(bucket, key, local_path)


def upload_from_path(bucket: str, key: str, local_path: str):
    s3_client.upload_file(local_path, bucket, key)
