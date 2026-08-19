from typing import Optional
from sqlalchemy import select, or_, asc, desc

from cooking_compass.core.db import SessionLocal
from cooking_compass.models.recipe import Recipe
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
    Asynchronous service to search recipes based on query string, scope, filters, pagination, and sorting.
    Excludes soft-deleted recipes using `deleted_at`.
    """
    async with SessionLocal() as session:
        query = select(Recipe)

        # Exclude soft-deleted recipes
        query = query.filter(Recipe.deleted_at.is_(None))

        # Filter by scope
        user_id = current_user.get("id") or current_user.get("user_id")
        if scope == "mine":
            query = query.filter(Recipe.user_id == user_id)
        else:
            query = query.filter(
                or_(
                    Recipe.visibility == "PUBLIC",
                    Recipe.user_id == user_id
                )
            )

        # Text search on name or description using ilike (case-insensitive)
        if q:
            search_filter = or_(
                Recipe.name.ilike(f"%{q}%"),
                Recipe.description.ilike(f"%{q}%")
            )
            query = query.filter(search_filter)

        # Filter by category_id if provided
        if category_id is not None:
            query = query.filter(Recipe.categories.any(category_id=category_id))

        # Filter by tag_id if provided
        if tag_id is not None:
            query = query.filter(Recipe.tags.any(tag_id=tag_id))

        # Execute query to get all matching items for counting and pagination
        result = await session.execute(query)
        all_recipes = result.scalars().unique().all()
        total = len(all_recipes)

        # Sorting
        sort_column = getattr(Recipe, sort_by, Recipe.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        # Pagination
        offset = (page - 1) * limit
        paginated_query = query.offset(offset).limit(limit)

        paginated_result = await session.execute(paginated_query)
        recipes = paginated_result.scalars().unique().all()

        total_pages = (total + limit - 1) // limit if limit > 0 else 1

        # Return response matching RecipeSearchResponse schema (which includes 'query')
        return RecipeSearchResponse(
            items=recipes,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            query=q
        )