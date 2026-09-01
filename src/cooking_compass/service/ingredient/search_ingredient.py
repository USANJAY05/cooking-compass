from sqlalchemy import select

from cooking_compass.core.db import SessionLocal
from cooking_compass.models.ingredients import Ingredient
from cooking_compass.utils.cache import (
    CacheNamespace,
    build_cache_key_from_data,
    cache_get,
    cache_set,
)


# Cache TTL: 5 minutes
INGREDIENT_SEARCH_CACHE_TTL = 300


async def search_ingredients_service(
    q: str,
    page: int,
    page_size: int,
):
    search_text = q.strip().lower()

    # Build a deterministic cache key from all parameters
    # that can affect the result.
    cache_key = await build_cache_key_from_data(
        CacheNamespace.INGREDIENTS,
        {
            "type": "search",
            "query": search_text,
            "page": page,
            "page_size": page_size,
        },
    )

    # Try Redis first
    cached_result = await cache_get(cache_key)

    if cached_result is not None:
        return cached_result

    # Cache miss → query PostgreSQL
    async with SessionLocal() as session:

        offset = (page - 1) * page_size

        query = (
            select(Ingredient)
            .where(
                Ingredient.name.ilike(f"{search_text}%")
            )
            .order_by(Ingredient.name)
            .offset(offset)
            .limit(page_size)
        )

        result = await session.execute(query)

        ingredients = result.scalars().all()

        # Convert SQLAlchemy models into cacheable data.
        response = [
            {
                "id": ingredient.id,
                "name": ingredient.name,
            }
            for ingredient in ingredients
        ]

    # Store the result in Redis
    await cache_set(
        cache_key,
        response,
        ttl=INGREDIENT_SEARCH_CACHE_TTL,
    )

    return response