# cooking_compass/utils/cache.py

import hashlib
import json
from enum import StrEnum
from typing import Any

from cooking_compass.core.redis import get_redis


# ============================================================
# Configuration
# ============================================================

DEFAULT_CACHE_TTL = 60 * 5  # 5 minutes


# ============================================================
# Cache namespaces
# ============================================================

class CacheNamespace(StrEnum):

    RECIPES = "recipes"

    ROUTINES = "routines"

    CATEGORIES = "categories"

    TAGS = "tags"

    USERS = "users"

    RATINGS = "ratings"

    IMAGES = "images"

    INGREDIENTS = "ingredients"


# ============================================================
# Internal key helpers
# ============================================================

def _version_key(
    namespace: CacheNamespace | str,
) -> str:

    return (
        f"cache:"
        f"{namespace}:"
        f"version"
    )


def _cache_prefix(
    namespace: CacheNamespace | str,
) -> str:

    return (
        f"cache:"
        f"{namespace}:"
    )


# ============================================================
# Namespace version
# ============================================================

async def get_namespace_version(
    namespace: CacheNamespace | str,
) -> int:

    redis = get_redis()

    key = _version_key(namespace)

    try:

        version = await redis.get(key)

        if version is None:

            created = await redis.set(
                key,
                "1",
                nx=True,
            )

            if created:
                return 1

            version = await redis.get(key)

        return int(version)

    except Exception:

        # Redis failure should never
        # break the API.
        return 1


# ============================================================
# Build cache key from a simple identifier
# ============================================================

async def build_cache_key(
    namespace: CacheNamespace | str,
    identifier: str,
) -> str:

    version = await get_namespace_version(
        namespace
    )

    return (
        f"{_cache_prefix(namespace)}"
        f"v{version}:"
        f"{identifier}"
    )


# ============================================================
# Build cache key from request data
# ============================================================

async def build_cache_key_from_data(
    namespace: CacheNamespace | str,
    data: dict[str, Any],
) -> str:

    serialized = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )

    digest = hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()

    return await build_cache_key(
        namespace,
        digest,
    )


# ============================================================
# GET
# ============================================================

async def cache_get(
    key: str,
) -> Any | None:

    redis = get_redis()

    try:

        value = await redis.get(key)

        if value is None:
            return None

        return json.loads(value)

    except Exception:

        # Redis failure = cache miss.
        return None


# ============================================================
# SET
# ============================================================

async def cache_set(
    key: str,
    value: Any,
    ttl: int = DEFAULT_CACHE_TTL,
) -> bool:

    redis = get_redis()

    try:

        await redis.set(
            key,
            json.dumps(
                value,
                default=str,
            ),
            ex=ttl,
        )

        return True

    except Exception:

        # Cache failure should not
        # break the API.
        return False


# ============================================================
# DELETE exact key
# ============================================================

async def cache_delete(
    key: str,
) -> bool:

    redis = get_redis()

    try:

        await redis.delete(key)

        return True

    except Exception:

        return False