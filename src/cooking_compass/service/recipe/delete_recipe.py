from datetime import datetime
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from cooking_compass.core.db import SessionLocal
from cooking_compass.models.recipe import Recipe


async def delete_recipe_service(
    recipe_id: int,
    current_user: dict,
) -> bool:
    """
    Asynchronous service to soft delete a recipe belonging to the current user
    by setting `deleted_at` to the current timestamp.
    Returns True if successfully deleted, False if the recipe was not found.
    """
    async with SessionLocal() as session:
        try:
            # 1. Get the recipe ensuring it belongs to the current user and is not already deleted
            result = await session.execute(
                select(Recipe).where(
                    Recipe.id == recipe_id,
                    Recipe.user_id == current_user["id"],
                    Recipe.deleted_at.is_(None),
                )
            )
            recipe = result.scalar_one_or_none()

            if recipe is None:
                return False

            # 2. Perform soft delete using `deleted_at`
            recipe.deleted_at = datetime.utcnow()

            await session.commit()
            return True

        except Exception:
            await session.rollback()
            raise