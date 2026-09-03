from sqlalchemy import select

from cooking_compass.core.db import SessionLocal
from cooking_compass.models.ingredients import Ingredient

from cooking_compass.utils.cache import (
    CacheNamespace,
    build_cache_key_from_data,
    cache_get,
    cache_set,
)


async def list_ingredients_service(
    page: int,
    page_size: int,
):
    # ========================================================
    # Cache key
    # ========================================================

    cache_key = await build_cache_key_from_data(
        CacheNamespace.INGREDIENTS,
        {
            "type": "list",
            "page": page,
            "page_size": page_size,
        },
    )

    # ========================================================
    # Check cache
    # ========================================================

    cached_result = await cache_get(
        cache_key
    )

    if cached_result is not None:
        return cached_result

    # ========================================================
    # Database
    # ========================================================

    async with SessionLocal() as session:

        offset = (
            page - 1
        ) * page_size

        query = (
            select(Ingredient)
            .order_by(
                Ingredient.name
            )
            .offset(offset)
            .limit(page_size)
        )

        result = await session.execute(
            query
        )

        ingredients = result.scalars().all()

    # ========================================================
    # Cache result
    # ========================================================

    response = [
        {
            "id": ingredient.id,
            "name": ingredient.name,
        }
        for ingredient in ingredients
    ]

    await cache_set(
        cache_key,
        response,
        ttl=300,
    )

    return response