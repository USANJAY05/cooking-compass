from cooking_compass.core.db import SessionLocal
from cooking_compass.models.recipe_ratings import RecipeRating
from sqlalchemy import select


async def create_or_update_rating_service(
    recipe_id: int,
    request,
    current_user: dict | object,
):
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
            # Check if rating already exists for this user and recipe
            result = await session.execute(
                select(RecipeRating).where(
                    RecipeRating.recipe_id == recipe_id,
                    RecipeRating.user_id == user_id,
                )
            )
            rating_obj = result.scalar_one_or_none()

            if rating_obj:
                # Update existing rating
                rating_obj.rating = request.rating
                if hasattr(request, "review") and request.review is not None:
                    rating_obj.review = request.review
            else:
                # Create new rating
                rating_obj = RecipeRating(
                    recipe_id=recipe_id,
                    user_id=user_id,
                    rating=request.rating,
                    review=getattr(request, "review", None),
                )
                session.add(rating_obj)

            await session.commit()
            await session.refresh(rating_obj)
            return rating_obj

        except Exception:
            await session.rollback()
            raise