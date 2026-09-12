from __future__ import annotations

import hashlib
import hmac
import os
from datetime import datetime, timezone
from urllib.parse import quote
from uuid import uuid4


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


def _hmac(key: bytes, value: str) -> bytes:
    return hmac.new(key, value.encode("utf-8"), hashlib.sha256).digest()


def _encode(value: str) -> str:
    return quote(value, safe="-_.~")


def generate_presigned_put_url(
    *,
    object_key: str,
    content_type: str,
    content_length: int,
    expires_in: int = UPLOAD_URL_TTL_SECONDS,
) -> str:
    """Generate a short-lived SigV4 PUT URL for Backblaze B2's S3 API."""
    endpoint, bucket, key_id, application_key, region = _required_config()

    now = datetime.now(timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")
    host = endpoint.removeprefix("https://").removeprefix("http://")

    canonical_uri = f"/{_encode(bucket)}/{quote(object_key, safe='/-_.~')}"
    credential_scope = f"{date_stamp}/{region}/s3/aws4_request"

    query = {
        "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
        "X-Amz-Credential": f"{key_id}/{credential_scope}",
        "X-Amz-Date": amz_date,
        "X-Amz-Expires": str(expires_in),
        "X-Amz-SignedHeaders": "content-length;content-type;host",
    }
    canonical_query = "&".join(
        f"{_encode(key)}={_encode(value)}" for key, value in sorted(query.items())
    )

    canonical_headers = (
        f"content-length:{content_length}\n"
        f"content-type:{content_type}\n"
        f"host:{host}\n"
    )
    signed_headers = "content-length;content-type;host"
    canonical_request = (
        f"PUT\n{canonical_uri}\n{canonical_query}\n"
        f"{canonical_headers}\n{signed_headers}\nUNSIGNED-PAYLOAD"
    )

    string_to_sign = (
        "AWS4-HMAC-SHA256\n"
        f"{amz_date}\n"
        f"{credential_scope}\n"
        f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    )

    signing_key = _hmac(
        _hmac(
            _hmac(
                _hmac(("AWS4" + application_key).encode("utf-8"), date_stamp),
                region,
            ),
            "s3",
        ),
        "aws4_request",
    )
    query["X-Amz-Signature"] = hmac.new(
        signing_key,
        string_to_sign.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    encoded_query = "&".join(
        f"{_encode(key)}={_encode(value)}" for key, value in sorted(query.items())
    )
    return f"{endpoint}{canonical_uri}?{encoded_query}"


def build_image_key() -> str:
    return f"images/{uuid4()}"
