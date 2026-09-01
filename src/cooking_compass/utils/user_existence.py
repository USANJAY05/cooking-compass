from cooking_compass.core.db import SessionLocal
from cooking_compass.models.users import User
from sqlalchemy import select

from cooking_compass.utils.cache import (
    CacheNamespace,
    build_cache_key,
    cache_get,
    cache_set,
)


# =========================================================
# CACHE CONFIG
# =========================================================

USER_EXISTENCE_CACHE_TTL = 300


async def user_existence(email: str) -> bool:
    """
    Check if a user with the given email exists in the database.

    Result is cached in Redis, since this is an existence check
    that doesn't change often and may be called repeatedly
    (e.g. once per request during auth resolution).
    """

    # ---------------------------------------------------------
    # Cache key
    # ---------------------------------------------------------
    #
    # Simple identifier-based key (no need for
    # build_cache_key_from_data / hashing here since the
    # identifier is already a single, safe string).

    cache_key = await build_cache_key(
        CacheNamespace.USERS,
        f"exists:{email}",
    )

    # ---------------------------------------------------------
    # Redis
    # ---------------------------------------------------------

    cached_result = await cache_get(
        cache_key
    )

    if cached_result is not None:

        return cached_result["exists"]

    # ---------------------------------------------------------
    # Database
    # ---------------------------------------------------------

    try:

        async with SessionLocal() as session:

            result = await session.execute(
                select(User).filter_by(
                    email=email
                )
            )

            user = result.scalars().first()

            exists = user is not None

    except Exception as e:

        raise RuntimeError(
            f"Database error while checking user existence: {e}"
        )

    # ---------------------------------------------------------
    # Cache result
    # ---------------------------------------------------------

    await cache_set(
        cache_key,
        {"exists": exists},
        ttl=USER_EXISTENCE_CACHE_TTL,
    )

    return exists