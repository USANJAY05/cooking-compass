from typing import Literal

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from cooking_compass.core.db import SessionLocal

from cooking_compass.models.recipe import Recipe
from cooking_compass.models.recipe_categories import RecipeCategory
from cooking_compass.models.recipe_tags import RecipeTag
from cooking_compass.models.recipe_ratings import RecipeRating
from cooking_compass.models.recipe_images import RecipeImage


async def get_recipes_service(
    scope: Literal["mine", "public"],
    category_id: int | None,
    tag_id: int | None,
    user_id: int | None,
    page: int,
    limit: int,
    sort_by: Literal[
        "created_at",
        "name",
        "rating",
        "cooking_time",
    ],
    sort_order: Literal["asc", "desc"],
    current_user: dict,
):
    async with SessionLocal() as session:

        # --------------------------------------------------
        # Base query
        # --------------------------------------------------
        query = select(Recipe).where(
            Recipe.deleted_at.is_(None)
        )

        # --------------------------------------------------
        # Scope
        # --------------------------------------------------
        if scope == "mine":
            query = query.where(
                Recipe.user_id == current_user["id"]
            )
        else:
            query = query.where(
                Recipe.visibility == "PUBLIC",
            )

        # --------------------------------------------------
        # User filter
        # --------------------------------------------------
        if user_id is not None:
            query = query.where(
                Recipe.user_id == user_id
            )

        # --------------------------------------------------
        # Category filter
        # --------------------------------------------------
        if category_id is not None:
            query = query.where(
                Recipe.categories.any(
                    RecipeCategory.category_id == category_id
                )
            )

        # --------------------------------------------------
        # Tag filter
        # --------------------------------------------------
        if tag_id is not None:
            query = query.where(
                Recipe.tags.any(
                    RecipeTag.tag_id == tag_id
                )
            )

        # --------------------------------------------------
        # Rating subquery
        # --------------------------------------------------
        rating_subquery = (
            select(
                func.coalesce(
                    func.avg(RecipeRating.rating),
                    0,
                )
            )
            .where(
                RecipeRating.recipe_id == Recipe.id
            )
            .correlate(Recipe)
            .scalar_subquery()
        )

        # --------------------------------------------------
        # Sorting
        # --------------------------------------------------
        if sort_by == "name":
            sort_column = Recipe.name

        elif sort_by == "cooking_time":
            sort_column = Recipe.cooking_time

        elif sort_by == "rating":
            sort_column = rating_subquery

        else:
            sort_column = Recipe.created_at

        if sort_order == "asc":
            query = query.order_by(
                sort_column.asc(),
                Recipe.id.asc(),
            )
        else:
            query = query.order_by(
                sort_column.desc(),
                Recipe.id.desc(),
            )

        # --------------------------------------------------
        # Count query
        # --------------------------------------------------
        count_query = (
            select(func.count(Recipe.id))
            .select_from(Recipe)
            .where(
                Recipe.deleted_at.is_(None)
            )
        )

        if scope == "mine":
            count_query = count_query.where(
                Recipe.user_id == current_user["id"]
            )
        else:
            count_query = count_query.where(
                Recipe.visibility == "PUBLIC",
            )

        if user_id is not None:
            count_query = count_query.where(
                Recipe.user_id == user_id
            )

        if category_id is not None:
            count_query = count_query.where(
                Recipe.categories.any(
                    RecipeCategory.category_id == category_id
                )
            )

        if tag_id is not None:
            count_query = count_query.where(
                Recipe.tags.any(
                    RecipeTag.tag_id == tag_id
                )
            )

        count_result = await session.execute(count_query)
        total = count_result.scalar_one()

        # --------------------------------------------------
        # Pagination
        # --------------------------------------------------
        offset = (page - 1) * limit

        query = query.offset(offset).limit(limit)

        # --------------------------------------------------
        # Load images for thumbnail
        # --------------------------------------------------
        query = query.options(
            selectinload(Recipe.images).selectinload(
                RecipeImage.image
            )
        )

        # --------------------------------------------------
        # Execute
        # --------------------------------------------------
        result = await session.execute(query)

        recipes = result.scalars().unique().all()

        # --------------------------------------------------
        # Build response
        # --------------------------------------------------
        items = []

        for recipe in recipes:

            thumbnail_url = None

            for recipe_image in recipe.images:

                if (
                    recipe_image.image_type == "THUMBNAIL"
                    and recipe_image.image is not None
                ):
                    storage_key = (
                        recipe_image.image.storage_key
                    )

                    if storage_key.startswith(
                        ("http://", "https://")
                    ):
                        thumbnail_url = storage_key

                    break

            items.append(
                {
                    "id": recipe.id,
                    "name": recipe.name,
                    "thumbnail_url": thumbnail_url,
                    "preparation_time": recipe.preparation_time,
                    "cooking_time": recipe.cooking_time,
                    "servings": int(recipe.servings),
                }
            )

        return {
            "items": items,
            "page": page,
            "limit": limit,
            "total": total,
        }