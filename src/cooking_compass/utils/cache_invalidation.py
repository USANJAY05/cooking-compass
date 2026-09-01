# cooking_compass/utils/cache_invalidation.py

from cooking_compass.core.redis import get_redis

from cooking_compass.utils.cache import (
    CacheNamespace,
)


# ============================================================
# Internal helper
# ============================================================

def _version_key(
    namespace: CacheNamespace | str,
) -> str:

    return (
        f"cache:"
        f"{namespace}:"
        f"version"
    )


# ============================================================
# Invalidate one or more namespaces
# ============================================================

async def invalidate(
    *namespaces: CacheNamespace | str,
) -> bool:

    if not namespaces:
        return True

    redis = get_redis()

    try:

        async with redis.pipeline(
            transaction=True
        ) as pipe:

            for namespace in namespaces:

                pipe.incr(
                    _version_key(namespace)
                )

            await pipe.execute()

        return True

    except Exception:

        # Cache invalidation failure should
        # never break a successful DB operation.
        return False


# ============================================================
# Recipe invalidation
# ============================================================

async def invalidate_recipe() -> bool:

    return await invalidate(
        CacheNamespace.RECIPES,
    )


# ============================================================
# Recipe + rating invalidation
# ============================================================

async def invalidate_recipe_with_rating() -> bool:

    return await invalidate(
        CacheNamespace.RECIPES,
        CacheNamespace.RATINGS,
    )


# ============================================================
# Recipe + image invalidation
# ============================================================

async def invalidate_recipe_with_image() -> bool:

    return await invalidate(
        CacheNamespace.RECIPES,
        CacheNamespace.IMAGES,
    )


# ============================================================
# Routine invalidation
# ============================================================

async def invalidate_routine() -> bool:

    return await invalidate(
        CacheNamespace.ROUTINES,
    )


# ============================================================
# Recipe + routine invalidation
# ============================================================

async def invalidate_recipe_and_routine() -> bool:

    return await invalidate(
        CacheNamespace.RECIPES,
        CacheNamespace.ROUTINES,
    )


# ============================================================
# Category invalidation
# ============================================================

async def invalidate_category() -> bool:

    return await invalidate(
        CacheNamespace.CATEGORIES,
        CacheNamespace.RECIPES,
    )


# ============================================================
# Tag invalidation
# ============================================================

async def invalidate_tag() -> bool:

    return await invalidate(
        CacheNamespace.TAGS,
        CacheNamespace.RECIPES,
    )


# ============================================================
# User invalidation
# ============================================================

async def invalidate_user() -> bool:

    return await invalidate(
        CacheNamespace.USERS,
    )


# ============================================================
# Ingredient invalidation
# ============================================================

async def invalidate_ingredient() -> bool:

    return await invalidate(
        CacheNamespace.INGREDIENTS,
    )


# ============================================================
# Invalidate everything
# ============================================================

async def invalidate_all() -> bool:

    return await invalidate(
        *CacheNamespace,
    )