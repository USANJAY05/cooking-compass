from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from cooking_compass.storage.b2 import (
    ALLOWED_IMAGE_TYPES,
    MAX_IMAGE_SIZE_BYTES,
    UPLOAD_URL_TTL_SECONDS,
    build_image_key,
    generate_presigned_put_url,
)
from cooking_compass.utils.ensure_user import ensure_user_exists


router = APIRouter(prefix="/images", tags=["images"])


class ImageUploadRequest(BaseModel):
    content_type: str = Field(description="MIME type of the optimized image")
    content_length: int = Field(gt=0, le=MAX_IMAGE_SIZE_BYTES)


class ImageUploadResponse(BaseModel):
    upload_url: str
    object_key: str
    content_type: str
    content_length: int
    expires_in: int
    required_headers: dict[str, str]


@router.post("/upload-url", response_model=ImageUploadResponse)
async def create_image_upload_url(
    payload: ImageUploadRequest,
    current_user: dict = Depends(ensure_user_exists),
):
    """Create a 5-minute PUT URL for direct browser -> storage upload."""
    if not current_user.get("sub"):
        raise HTTPException(status_code=400, detail="Authenticated user subject is missing")

    content_type = payload.content_type.lower().strip()
    extension = ALLOWED_IMAGE_TYPES.get(content_type)
    if not extension:
        raise HTTPException(
            status_code=415,
            detail={
                "message": "Unsupported image type",
                "allowed_types": sorted(ALLOWED_IMAGE_TYPES),
            },
        )

    object_key = f"{build_image_key(current_user['id'])}{extension}"
    try:
        upload_url = generate_presigned_put_url(
            object_key=object_key,
            content_type=content_type,
            content_length=payload.content_length,
            expires_in=UPLOAD_URL_TTL_SECONDS,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    # Content-Length is intentionally omitted. Browsers control this header and
    # Fetch does not allow application code to set it. The requested length is
    # still returned as metadata and is verified against the actual object size
    # when the recipe is created.
    return ImageUploadResponse(
        upload_url=upload_url,
        object_key=object_key,
        content_type=content_type,
        content_length=payload.content_length,
        expires_in=UPLOAD_URL_TTL_SECONDS,
        required_headers={
            "Content-Type": content_type,
        },
    )
