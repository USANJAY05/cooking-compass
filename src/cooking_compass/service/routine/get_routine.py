from fastapi import HTTPException, status

from sqlalchemy import (
    select,
    func,
    asc,
    desc,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cooking_compass.models.routines import Routine
from cooking_compass.models.routine_items import RoutineItem

from cooking_compass.utils.cache import (
    CacheNamespace,
    build_cache_key_from_data,
    cache_get,
    cache_set,
)


# =========================================================
# CACHE CONFIG
# =========================================================

ROUTINE_CACHE_TTL = 300


# =========================================================
# SERIALIZATION HELPERS
# =========================================================
#
# cache_set() stores responses as JSON (json.dumps(..., default=str)).
# That means datetime/date objects go IN as ISO strings, but if we
# don't also convert them on the way OUT of the DB path, a fresh
# DB response and a cache-hit response end up with different Python
# types for the same field (datetime object vs str). This silently
# breaks response_model validation / equality checks / anything
# downstream that assumes a consistent shape.
#
# Fix: always convert date/datetime fields to ISO strings ourselves,
# in the serializer, before either returning or caching. That way
# the DB path and the cache-hit path are byte-for-byte identical.

def _iso(value):
    """Convert datetime/date to ISO string; pass through None/str unchanged."""

    if value is None:
        return None

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return value


# =========================================================
# ROUTINE SUMMARY SERIALIZER
# =========================================================

def serialize_routine_summary(
    routine: Routine,
) -> dict:
    """
    Serialize a Routine for list/search responses.

    This matches RoutineSummaryComponent.
    """

    return {
        "id": routine.id,
        "name": routine.name,
        "description": routine.description,
        "created_at": _iso(routine.created_at),
        "updated_at": _iso(routine.updated_at),
    }


# =========================================================
# ROUTINE DETAIL SERIALIZER
# =========================================================

def serialize_routine_detail(
    routine: Routine,
) -> dict:
    """
    Serialize a Routine for the detail endpoint.

    This matches RoutineDetailResponse.
    """

    # ---------------------------------------------------------
    # Routine items
    # ---------------------------------------------------------

    items = getattr(
        routine,
        "items",
        [],
    ) or []

    recipes = []

    for item in items:

        recipe = getattr(
            item,
            "recipe",
            None,
        )

        recipes.append(
            {
                "recipe_id": item.recipe_id,

                "recipe_name": (
                    recipe.name
                    if recipe is not None
                    else ""
                ),

                "recipe_thumbnail_url": None,

                "quantity": item.quantity,

                "quantity_unit": item.quantity_type,
            }
        )

    # ---------------------------------------------------------
    # Recurrence
    # ---------------------------------------------------------

    recurrence = getattr(
        routine,
        "recurrence",
        None,
    )

    recurrence_data = None

    if recurrence is not None:

        # -----------------------------------------------------
        # Days of week
        # -----------------------------------------------------

        days_of_week = getattr(
            recurrence,
            "days_of_week",
            None,
        ) or []

        if isinstance(
            days_of_week,
            str,
        ):

            if days_of_week.strip():

                days_of_week = [
                    int(day.strip())
                    for day in days_of_week.split(",")
                    if day.strip()
                ]

            else:

                days_of_week = []

        # -----------------------------------------------------
        # Recurrence response
        # -----------------------------------------------------

        recurrence_data = {
            "frequency": recurrence.frequency,

            # RoutineRecurrence does not have an interval
            # column, so the API currently defaults to 1.
            "interval": 1,

            "days_of_week": days_of_week,

            "start_date": _iso(recurrence.start_date),

            "end_date": _iso(
                getattr(
                    recurrence,
                    "end_date",
                    None,
                )
            ),

            "occurrence_count": getattr(
                recurrence,
                "occurrence_count",
                None,
            ),
        }

    # ---------------------------------------------------------
    # Final response
    # ---------------------------------------------------------

    return {
        "id": routine.id,

        "name": routine.name,

        "description": routine.description,

        "status": routine.status,

        "recipes": recipes,

        "recurrence": recurrence_data,
    }


# =========================================================
# GET ROUTINE BY ID
# =========================================================

async def get_routine(
    db: AsyncSession,
    user_id: int,
    routine_id: int,
):
    """
    Get a single routine.

    Cache is user-specific because the routine belongs
    to a user.
    """

    # ---------------------------------------------------------
    # Cache key
    # ---------------------------------------------------------

    cache_key = await build_cache_key_from_data(
        CacheNamespace.ROUTINES,
        {
            "type": "detail",
            "user_id": user_id,
            "routine_id": routine_id,
        },
    )

    # ---------------------------------------------------------
    # Redis
    # ---------------------------------------------------------

    cached_result = await cache_get(
        cache_key
    )

    if cached_result is not None:

        return cached_result

    # ---------------------------------------------------------
    # Database
    # ---------------------------------------------------------

    routine = await db.scalar(
        select(Routine)
        .where(
            Routine.id == routine_id,
            Routine.user_id == user_id,
        )
        .options(
            selectinload(
                Routine.items
            ).selectinload(
                RoutineItem.recipe
            ),

            selectinload(
                Routine.recurrence
            ),
        )
    )

    # ---------------------------------------------------------
    # Not found
    # ---------------------------------------------------------

    if routine is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Routine not found",
        )

    # ---------------------------------------------------------
    # Serialize
    # ---------------------------------------------------------

    response = serialize_routine_detail(
        routine
    )

    # ---------------------------------------------------------
    # Cache
    # ---------------------------------------------------------

    await cache_set(
        cache_key,
        response,
        ttl=ROUTINE_CACHE_TTL,
    )

    return response


# =========================================================
# GET ROUTINES
# =========================================================

async def get_routines(
    db: AsyncSession,
    user_id: int,
    scope: str = "mine",
    page: int = 1,
    limit: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
):
    """
    Get paginated routines.

    Cache key contains every parameter that changes
    the result.
    """

    # ---------------------------------------------------------
    # Cache key
    # ---------------------------------------------------------

    cache_key = await build_cache_key_from_data(
        CacheNamespace.ROUTINES,
        {
            "type": "list",
            "user_id": user_id,
            "scope": scope,
            "page": page,
            "limit": limit,
            "sort_by": sort_by,
            "sort_order": sort_order,
        },
    )

    # ---------------------------------------------------------
    # Redis
    # ---------------------------------------------------------

    cached_result = await cache_get(
        cache_key
    )

    if cached_result is not None:

        return (
            cached_result["items"],
            cached_result["total"],
        )

    # ---------------------------------------------------------
    # Base query
    # ---------------------------------------------------------

    query = select(Routine)

    # ---------------------------------------------------------
    # Scope
    # ---------------------------------------------------------

    if scope == "mine":

        query = query.where(
            Routine.user_id == user_id
        )

    # ---------------------------------------------------------
    # Sorting
    # ---------------------------------------------------------

    sort_column = getattr(
        Routine,
        sort_by,
        Routine.created_at,
    )

    if sort_order == "asc":

        query = query.order_by(
            asc(sort_column)
        )

    else:

        query = query.order_by(
            desc(sort_column)
        )

    # ---------------------------------------------------------
    # Count
    # ---------------------------------------------------------

    total = await db.scalar(
        select(func.count())
        .select_from(
            query.subquery()
        )
    )

    total = total or 0

    # ---------------------------------------------------------
    # Pagination
    # ---------------------------------------------------------

    result = await db.scalars(
        query
        .offset(
            (page - 1) * limit
        )
        .limit(limit)
    )

    routines = result.all()

    # ---------------------------------------------------------
    # Serialize
    # ---------------------------------------------------------

    items = [
        serialize_routine_summary(
            routine
        )
        for routine in routines
    ]

    # ---------------------------------------------------------
    # Cache response
    # ---------------------------------------------------------

    response = {
        "items": items,
        "total": total,
    }

    await cache_set(
        cache_key,
        response,
        ttl=ROUTINE_CACHE_TTL,
    )

    # ---------------------------------------------------------
    # Existing service return format
    # ---------------------------------------------------------

    return (
        items,
        total,
    )


# =========================================================
# SEARCH ROUTINES
# =========================================================

async def search_routines(
    db: AsyncSession,
    user_id: int,
    q: str,
    scope: str = "mine",
    page: int = 1,
    limit: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
):
    """
    Search routines.

    Cache key contains the search query and all
    parameters affecting the result.
    """

    # ---------------------------------------------------------
    # Normalize query
    # ---------------------------------------------------------

    normalized_query = q.strip().lower()

    # ---------------------------------------------------------
    # Cache key
    # ---------------------------------------------------------

    cache_key = await build_cache_key_from_data(
        CacheNamespace.ROUTINES,
        {
            "type": "search",
            "user_id": user_id,
            "query": normalized_query,
            "scope": scope,
            "page": page,
            "limit": limit,
            "sort_by": sort_by,
            "sort_order": sort_order,
        },
    )

    # ---------------------------------------------------------
    # Redis
    # ---------------------------------------------------------

    cached_result = await cache_get(
        cache_key
    )

    if cached_result is not None:

        return (
            cached_result["items"],
            cached_result["total"],
        )

    # ---------------------------------------------------------
    # Query
    # ---------------------------------------------------------

    query = select(Routine).where(
        Routine.name.ilike(
            f"%{normalized_query}%"
        )
    )

    # ---------------------------------------------------------
    # Scope
    # ---------------------------------------------------------

    if scope == "mine":

        query = query.where(
            Routine.user_id == user_id
        )

    # ---------------------------------------------------------
    # Sorting
    # ---------------------------------------------------------

    sort_column = getattr(
        Routine,
        sort_by,
        Routine.created_at,
    )

    if sort_order == "asc":

        query = query.order_by(
            asc(sort_column)
        )

    else:

        query = query.order_by(
            desc(sort_column)
        )

    # ---------------------------------------------------------
    # Count
    # ---------------------------------------------------------

    total = await db.scalar(
        select(func.count())
        .select_from(
            query.subquery()
        )
    )

    total = total or 0

    # ---------------------------------------------------------
    # Pagination
    # ---------------------------------------------------------

    result = await db.scalars(
        query
        .offset(
            (page - 1) * limit
        )
        .limit(limit)
    )

    routines = result.all()

    # ---------------------------------------------------------
    # Serialize
    # ---------------------------------------------------------

    items = [
        serialize_routine_summary(
            routine
        )
        for routine in routines
    ]

    # ---------------------------------------------------------
    # Cache response
    # ---------------------------------------------------------

    response = {
        "items": items,
        "total": total,
    }

    await cache_set(
        cache_key,
        response,
        ttl=ROUTINE_CACHE_TTL,
    )

    # ---------------------------------------------------------
    # Existing service return format
    # ---------------------------------------------------------

    return (
        items,
        total,
    )