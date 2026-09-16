from botocore.exceptions import ClientError
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from cooking_compass.core.db import SessionLocal
from cooking_compass.models.images import Image
from cooking_compass.models.instruction_images import InstructionImage
from cooking_compass.models.recipe import Recipe
from cooking_compass.models.recipe_categories import RecipeCategory
from cooking_compass.models.recipe_images import RecipeImage
from cooking_compass.models.recipe_ingredients import RecipeIngredient
from cooking_compass.models.recipe_instructions import RecipeInstruction
from cooking_compass.models.recipe_tags import RecipeTag
from cooking_compass.models.tags import Tag
from cooking_compass.schema.recipe.components_schema import to_grams
from cooking_compass.storage.b2 import (
    ALLOWED_IMAGE_TYPES,
    head_object,
)


async def _get_or_create_tag_ids(
    session,
    tag_names: list[str],
) -> list[int]:
    """Get existing tag IDs and create missing tags safely."""
    seen = set()
    normalized = []

    for name in tag_names:
        clean = name.strip().lower()
        if clean and clean not in seen:
            seen.add(clean)
            normalized.append(clean)

    if not normalized:
        return []

    result = await session.execute(
        select(Tag).where(Tag.name.in_(normalized))
    )

    existing = {tag.name: tag.id for tag in result.scalars().all()}

    missing = [name for name in normalized if name not in existing]

    for name in missing:
        try:
            async with session.begin_nested():
                tag = Tag(name=name)
                session.add(tag)
                await session.flush()
            existing[name] = tag.id
        except IntegrityError:
            result = await session.execute(
                select(Tag).where(Tag.name == name)
            )
            tag = result.scalars().first()
            if tag is None:
                raise
            existing[name] = tag.id

    return [existing[name] for name in normalized]


def _validate_image_reference(image_reference, *, user_id: int) -> None:
    """Validate that an image reference belongs to the authenticated user."""
    object_key = image_reference.object_key
    expected_prefix = f"users/{user_id}/images/"

    if not object_key.startswith(expected_prefix):
        raise HTTPException(
            status_code=400,
            detail="Image object_key does not belong to the authenticated user",
        )

    content_type = image_reference.content_type.lower().strip()
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported image type: {content_type}",
        )


def _read_uploaded_image_metadata(image_reference, *, user_id: int) -> tuple[str, int]:
    """Verify the uploaded object exists and return its actual type and size."""
    _validate_image_reference(image_reference, user_id=user_id)

    try:
        metadata = head_object(object_key=image_reference.object_key)
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code in {"404", "NoSuchKey", "NotFound"}:
            raise HTTPException(
                status_code=400,
                detail="Uploaded image was not found in object storage",
            ) from exc
        raise HTTPException(
            status_code=503,
            detail="Unable to verify uploaded image",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    actual_size = int(metadata.get("ContentLength", 0))
    actual_type = str(
        metadata.get("ContentType") or image_reference.content_type
    ).lower().strip()
    expected_type = image_reference.content_type.lower().strip()

    if actual_size <= 0 or actual_size != image_reference.content_length:
        raise HTTPException(
            status_code=400,
            detail="Uploaded image size does not match the upload metadata",
        )

    if actual_type != expected_type:
        raise HTTPException(
            status_code=400,
            detail="Uploaded image content type does not match the upload metadata",
        )

    return actual_type, actual_size


def _create_image_record(session, *, image_reference, user_id: int) -> Image:
    """Verify an uploaded object and create its database image record."""
    content_type, content_length = _read_uploaded_image_metadata(
        image_reference,
        user_id=user_id,
    )

    image = Image(
        storage_key=image_reference.object_key,
        mime_type=content_type,
        file_size=content_length,
    )
    session.add(image)
    return image


async def create_recipe_service(request, current_user: dict):
    """
    Create a recipe and all related records in one transaction.

    Images are uploaded directly from the client to S3-compatible storage
    using presigned PUT URLs. This transaction only receives object keys,
    verifies those objects exist, and creates the database associations.
    """
    user_id = current_user["id"]

    recipe_data = request.model_dump(
        exclude={
            "ingredients",
            "instructions",
            "category_ids",
            "tag_names",
            "thumbnail_image",
        }
    )

    if request.cooked_weight_amount is not None:
        recipe_data["cooked_weight_grams"] = to_grams(
            request.cooked_weight_amount,
            request.cooked_weight_unit,
        )

    async with SessionLocal() as session:
        try:
            recipe = Recipe(
                **recipe_data,
                user_id=user_id,
            )
            session.add(recipe)
            await session.flush()

            if request.category_ids:
                session.add_all(
                    RecipeCategory(
                        recipe_id=recipe.id,
                        category_id=category_id,
                    )
                    for category_id in request.category_ids
                )

            if request.ingredients:
                session.add_all(
                    RecipeIngredient(
                        recipe_id=recipe.id,
                        ingredient_id=ingredient.ingredient_id,
                        quantity=ingredient.quantity,
                        unit=ingredient.unit,
                        display_order=ingredient.display_order,
                    )
                    for ingredient in request.ingredients
                )

            for step in request.instructions:
                instruction = RecipeInstruction(
                    recipe_id=recipe.id,
                    step_number=step.step_number,
                    instruction_text=step.instruction_text,
                    timer_seconds=step.timer_seconds,
                    tip=step.tip,
                    reference_recipe_id=step.reference_recipe_id,
                )
                session.add(instruction)
                await session.flush()

                if step.reference_image is not None:
                    image = _create_image_record(
                        session,
                        image_reference=step.reference_image,
                        user_id=user_id,
                    )
                    await session.flush()
                    session.add(
                        InstructionImage(
                            instruction_id=instruction.id,
                            image_id=image.id,
                            display_order=1,
                        )
                    )

            if request.thumbnail_image is not None:
                image = _create_image_record(
                    session,
                    image_reference=request.thumbnail_image,
                    user_id=user_id,
                )
                await session.flush()
                session.add(
                    RecipeImage(
                        recipe_id=recipe.id,
                        image_id=image.id,
                        image_type="THUMBNAIL",
                        display_order=1,
                    )
                )

            tag_ids = await _get_or_create_tag_ids(
                session,
                request.tag_names,
            )

            if tag_ids:
                session.add_all(
                    RecipeTag(
                        recipe_id=recipe.id,
                        tag_id=tag_id,
                    )
                    for tag_id in tag_ids
                )

            await session.commit()
            await session.refresh(recipe)
            return recipe

        except Exception:
            await session.rollback()
            raise
