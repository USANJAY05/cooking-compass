from functools import wraps
import inspect

from fastapi import HTTPException
from sqlalchemy import select

from cooking_compass.core.db import SessionLocal
from cooking_compass.models.users import User

from .create_user import create_user

from cooking_compass.utils.cache import (
    CacheNamespace,
    build_cache_key,
    cache_get,
    cache_set,
)


# =========================================================
# CACHE CONFIG
# =========================================================

USER_ID_CACHE_TTL = 300


async def _resolve_user_id(email: str) -> int:
    """
    Resolve a user's internal DB id from their email.

    Cached in Redis, since this previously ran a full
    User row SELECT on every single request to any route
    decorated with @user_exist (cart, routine, recipe).
    """

    # ---------------------------------------------------------
    # Cache key
    # ---------------------------------------------------------

    cache_key = await build_cache_key(
        CacheNamespace.USERS,
        f"id:{email}",
    )

    # ---------------------------------------------------------
    # Redis
    # ---------------------------------------------------------

    cached_result = await cache_get(
        cache_key
    )

    if cached_result is not None:

        return cached_result["id"]

    # ---------------------------------------------------------
    # Database
    # ---------------------------------------------------------

    async with SessionLocal() as session:

        result = await session.execute(
            select(User).filter_by(
                email=email
            )
        )

        user = result.scalars().first()

        if not user:

            # create_user needs the full current_user dict,
            # not just the email, so the caller (wrapper below)
            # handles creation. This helper only ever runs
            # against an already-existing user.
            raise LookupError(
                f"No user found for email={email}"
            )

        user_id = user.id

    # ---------------------------------------------------------
    # Cache result
    # ---------------------------------------------------------

    await cache_set(
        cache_key,
        {"id": user_id},
        ttl=USER_ID_CACHE_TTL,
    )

    return user_id


def user_exist(func):

    @wraps(func)
    async def wrapper(*args, **kwargs):

        current_user = kwargs.get("current_user")

        if not current_user or not current_user.get("email"):

            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "message": "User does not exist in context",
                },
            )

        email = current_user.get("email")

        # -------------------------------------------------------
        # Try cached / DB lookup first
        # -------------------------------------------------------

        try:

            user_id = await _resolve_user_id(email)

        except LookupError:

            # -----------------------------------------------------
            # User doesn't exist yet — create, then resolve again.
            # This path only runs once per new user, so it's fine
            # for it to hit the DB directly (not cached).
            # -----------------------------------------------------

            async with SessionLocal() as session:

                user = await create_user(current_user)

                if user is None:

                    result = await session.execute(
                        select(User).filter_by(
                            email=email
                        )
                    )

                    user = result.scalars().first()

            user_id = user.id

            # Cache it now that the user exists.
            cache_key = await build_cache_key(
                CacheNamespace.USERS,
                f"id:{email}",
            )

            await cache_set(
                cache_key,
                {"id": user_id},
                ttl=USER_ID_CACHE_TTL,
            )

        current_user["id"] = user_id
        kwargs["current_user"] = current_user

        if inspect.iscoroutinefunction(func):
            return await func(*args, **kwargs)

        return func(*args, **kwargs)

    return wrapper