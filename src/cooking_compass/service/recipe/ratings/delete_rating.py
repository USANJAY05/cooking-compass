from cooking_compass.core.db import SessionLocal
from cooking_compass.models.recipe_ratings import RecipeRating
from sqlalchemy import select


async def delete_rating_service(
    recipe_id: int,
    current_user: dict | object,
) -> bool:
    # Safely resolve user_id
    user_id = None
    if isinstance(current_user, dict):
        user_id = (
            current_user.get("id")
            or current_user.get("user_id")
            or current_user.get("sub")
        )
    else:
        user_id = (
            getattr(current_user, "id", None)
            or getattr(current_user, "user_id", None)
            or getattr(current_user, "sub", None)
        )

    if user_id is None:
        raise ValueError(f"Unable to extract user id from current_user: {current_user}")

    async with SessionLocal() as session:
        try:
            result = await session.execute(
                select(RecipeRating).where(
                    RecipeRating.recipe_id == recipe_id,
                    RecipeRating.user_id == user_id,
                )
            )
            rating_obj = result.scalar_one_or_none()

            if not rating_obj:
                return False

            await session.delete(rating_obj)
            await session.commit()
            return True

        except Exception:
            await session.rollback()
            raise