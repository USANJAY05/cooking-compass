from __future__ import annotations

import os
from uuid import uuid4

import boto3
from botocore.config import Config


B2_REGION = os.getenv("B2_REGION", "us-east-005")
B2_ENDPOINT = os.getenv("B2_ENDPOINT", f"https://s3.{B2_REGION}.backblazeb2.com")
B2_BUCKET = os.getenv("B2_BUCKET")
B2_KEY_ID = os.getenv("B2_KEY_ID")
B2_APPLICATION_KEY = os.getenv("B2_APPLICATION_KEY")

UPLOAD_URL_TTL_SECONDS = 300
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/heic": ".heic",
}


def _required_config() -> tuple[str, str, str, str, str]:
    values = {
        "B2_ENDPOINT": B2_ENDPOINT,
        "B2_BUCKET": B2_BUCKET,
        "B2_KEY_ID": B2_KEY_ID,
        "B2_APPLICATION_KEY": B2_APPLICATION_KEY,
        "B2_REGION": B2_REGION,
    }
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise RuntimeError(f"Missing Backblaze B2 configuration: {', '.join(missing)}")
    return (
        B2_ENDPOINT.rstrip("/"),
        B2_BUCKET,  # type: ignore[return-value]
        B2_KEY_ID,  # type: ignore[return-value]
        B2_APPLICATION_KEY,  # type: ignore[return-value]
        B2_REGION,
    )


def _s3_client():
    endpoint, _, key_id, application_key, region = _required_config()
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=key_id,
        aws_secret_access_key=application_key,
        region_name=region,
        config=Config(signature_version="s3v4"),
    )


def generate_presigned_put_url(
    *,
    object_key: str,
    content_type: str,
    content_length: int,
    expires_in: int = UPLOAD_URL_TTL_SECONDS,
) -> str:
    """Generate a short-lived SigV4 PUT URL for Backblaze B2's S3 API."""
    _, bucket, _, _, _ = _required_config()
    return _s3_client().generate_presigned_url(
        "put_object",
        Params={
            "Bucket": bucket,
            "Key": object_key,
            "ContentType": content_type,
            "ContentLength": content_length,
        },
        ExpiresIn=expires_in,
        HttpMethod="PUT",
    )


def build_image_key() -> str:
    return f"images/{uuid4()}"
