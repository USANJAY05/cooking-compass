from __future__ import annotations

from uuid import uuid4

import boto3
from botocore.config import Config

from cooking_compass.core.config import (
    STORAGE_ACCESS_KEY_ID,
    STORAGE_BUCKET,
    STORAGE_ENDPOINT,
    STORAGE_REGION,
    STORAGE_SECRET_ACCESS_KEY,
)


UPLOAD_URL_TTL_SECONDS = 300
GET_URL_TTL_SECONDS = 3600
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/heic": ".heic",
}


def _required_config() -> tuple[str, str, str, str, str]:
    values = {
        "STORAGE_ENDPOINT": STORAGE_ENDPOINT,
        "STORAGE_BUCKET": STORAGE_BUCKET,
        "STORAGE_ACCESS_KEY_ID": STORAGE_ACCESS_KEY_ID,
        "STORAGE_SECRET_ACCESS_KEY": STORAGE_SECRET_ACCESS_KEY,
        "STORAGE_REGION": STORAGE_REGION,
    }
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise RuntimeError(
            f"Missing object storage configuration: {', '.join(missing)}"
        )
    return (
        STORAGE_ENDPOINT.rstrip("/"),  # type: ignore[union-attr]
        STORAGE_BUCKET,  # type: ignore[return-value]
        STORAGE_ACCESS_KEY_ID,  # type: ignore[return-value]
        STORAGE_SECRET_ACCESS_KEY,  # type: ignore[return-value]
        STORAGE_REGION,  # type: ignore[return-value]
    )


def _s3_client():
    endpoint, _, access_key_id, secret_access_key, region = _required_config()
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
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
    """Generate a browser-compatible SigV4 PUT URL for S3-compatible storage.

    Content-Length is deliberately not included in the signed request headers.
    Browsers control Content-Length and Fetch does not allow web applications to
    set it programmatically. The requested size is still validated by the API,
    and the actual uploaded object's size is verified with HEAD before the image
    is persisted to the database.
    """
    _, bucket, _, _, _ = _required_config()
    return _s3_client().generate_presigned_url(
        "put_object",
        Params={
            "Bucket": bucket,
            "Key": object_key,
            "ContentType": content_type,
        },
        ExpiresIn=expires_in,
        HttpMethod="PUT",
    )


def generate_presigned_get_url(
    *,
    object_key: str,
    expires_in: int = GET_URL_TTL_SECONDS,
) -> str:
    """Generate a short-lived URL for reading an image from object storage."""
    _, bucket, _, _, _ = _required_config()
    return _s3_client().generate_presigned_url(
        "get_object",
        Params={
            "Bucket": bucket,
            "Key": object_key,
        },
        ExpiresIn=expires_in,
        HttpMethod="GET",
    )


def head_object(*, object_key: str) -> dict:
    """Return metadata for an uploaded object."""
    _, bucket, _, _, _ = _required_config()
    return _s3_client().head_object(
        Bucket=bucket,
        Key=object_key,
    )


def build_image_key(user_id: int) -> str:
    return f"users/{user_id}/images/{uuid4()}"
