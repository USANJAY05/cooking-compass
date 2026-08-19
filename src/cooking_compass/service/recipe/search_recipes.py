from typing import Optional

from sqlalchemy import select, or_, asc, desc, func
from sqlalchemy.orm import selectinload

from cooking_compass.core.db import SessionLocal
from cooking_compass.models.recipe import Recipe
from cooking_compass.models.recipe_images import RecipeImage
from cooking_compass.models.recipe_ratings import RecipeRating
from cooking_compass.schema.recipe.response_schema import RecipeSearchResponse


async def search_recipes_service(
    current_user: dict,
    q: str,
    scope: str = "public",
    category_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    page: int = 1,
    limit: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> RecipeSearchResponse:
    """
    Search recipes by query string, scope, filters, pagination, and sorting.
    Excludes soft-deleted recipes using `deleted_at`.
    """

    async with SessionLocal() as session:

        user_id = current_user.get("id") or current_user.get("user_id")

        # --------------------------------------------------
        # Rating subquery — used for sort_by="rating"
        # --------------------------------------------------
        rating_subquery = (
            select(
                func.coalesce(func.avg(RecipeRating.rating), 0)
            )
            .where(RecipeRating.recipe_id == Recipe.id)
            .correlate(Recipe)
            .scalar_subquery()
        )

        # --------------------------------------------------
        # Base query
        # --------------------------------------------------
        query = select(Recipe).where(Recipe.deleted_at.is_(None))

        # Scope
        if scope == "mine":
            query = query.where(Recipe.user_id == user_id)
        else:
            query = query.where(
                or_(
                    Recipe.visibility == "PUBLIC",
                    Recipe.user_id == user_id,
                )
            )

        # Text search
        if q:
            query = query.where(
                or_(
                    Recipe.name.ilike(f"%{q}%"),
                    Recipe.description.ilike(f"%{q}%"),
                )
            )

        # Category filter
        if category_id is not None:
            query = query.where(
                Recipe.categories.any(category_id=category_id)
            )

        # Tag filter
        if tag_id is not None:
            query = query.where(
                Recipe.tags.any(tag_id=tag_id)
            )

        # --------------------------------------------------
        # Count (before pagination)
        # --------------------------------------------------
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await session.execute(count_query)
        total = count_result.scalar_one()

        # --------------------------------------------------
        # Sorting
        # --------------------------------------------------
        if sort_by == "rating":
            sort_column = rating_subquery
        else:
            sort_column = getattr(Recipe, sort_by, Recipe.created_at)

        if sort_order.lower() == "asc":
            query = query.order_by(sort_column.asc(), Recipe.id.asc())
        else:
            query = query.order_by(sort_column.desc(), Recipe.id.desc())

        # --------------------------------------------------
        # Pagination
        # --------------------------------------------------
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        # --------------------------------------------------
        # Load images for thumbnail
        # --------------------------------------------------
        query = query.options(
            selectinload(Recipe.images).selectinload(RecipeImage.image)
        )

        result = await session.execute(query)
        recipes = result.scalars().unique().all()

        # --------------------------------------------------
        # Ratings for this page (one query, not one per recipe)
        # --------------------------------------------------
        recipe_ids = [recipe.id for recipe in recipes]

        ratings_by_recipe = {}

        if recipe_ids:
            rating_rows = await session.execute(
                select(
                    RecipeRating.recipe_id,
                    func.coalesce(func.avg(RecipeRating.rating), 0),
                    func.count(RecipeRating.id),
                )
                .where(RecipeRating.recipe_id.in_(recipe_ids))
                .group_by(RecipeRating.recipe_id)
            )

            for recipe_id, average, count in rating_rows.all():
                ratings_by_recipe[recipe_id] = {
                    "average": float(average or 0),
                    "count": count,
                }

        # --------------------------------------------------
        # Build response items
        # --------------------------------------------------
        items = []

        for recipe in recipes:

            thumbnail_url = None

            for recipe_image in recipe.images:

                if (
                    recipe_image.image_type == "THUMBNAIL"
                    and recipe_image.image is not None
                ):
                    storage_key = recipe_image.image.storage_key

                    if storage_key.startswith(("http://", "https://")):
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
                    "rating": ratings_by_recipe.get(
                        recipe.id,
                        {"average": 0.0, "count": 0},
                    ),
                }
            )

        return RecipeSearchResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            query=q,
        )