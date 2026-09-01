from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)

from sqlalchemy.orm import Session

from cooking_compass.auth.keycloak import get_current_user
from cooking_compass.core.db import get_db
from cooking_compass.utils.check_user_exist import user_exist

from cooking_compass.utils.cache_invalidation import (
    invalidate_routine,
)

from cooking_compass.schema.routine.request_schema import (
    CreateRoutineRequest,
    UpdateRoutineRequest,
)

from cooking_compass.schema.routine.response_schema import (
    DeleteRoutineResponse,
    RoutineDetailResponse,
    RoutineListResponse,
    RoutineSearchResponse,
)

from cooking_compass.service.routine.get_routine import (
    get_routines as get_routines_service,
    search_routines as search_routines_service,
    get_routine as get_routine_service,
)

from cooking_compass.service.routine.create_routine import (
    create_routine as create_routine_service,
)

from cooking_compass.service.routine.update_routine import (
    update_routine as update_routine_service,
)

from cooking_compass.service.routine.delete_routine import (
    delete_routine as delete_routine_service,
)


router = APIRouter(
    prefix="/routines",
    tags=["ROUTINES"],
)


def _user_id(current_user: dict) -> int:
    return current_user["id"]


# =========================================================
# GET /routines
# =========================================================

@router.get(
    "/",
    response_model=RoutineListResponse,
)
@user_exist
async def get_routines(
    scope: str = Query(
        default="mine",
        description="Routine scope: mine or feed",
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    sort_by: str = Query(
        default="created_at",
    ),
    sort_order: str = Query(
        default="desc",
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    items, total = await get_routines_service(
        db=db,
        user_id=_user_id(current_user),
        scope=scope,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return RoutineListResponse(
        items=items,
        page=page,
        limit=limit,
        total=total,
    )


# =========================================================
# GET /routines/search
# =========================================================

@router.get(
    "/search",
    response_model=RoutineSearchResponse,
)
@user_exist
def search_routines(
    q: str = Query(
        ...,
        min_length=1,
        max_length=255,
    ),
    scope: str = Query(
        default="mine",
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    sort_by: str = Query(
        default="created_at",
    ),
    sort_order: str = Query(
        default="desc",
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    items, total = search_routines_service(
        db=db,
        user_id=_user_id(current_user),
        q=q,
        scope=scope,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return RoutineSearchResponse(
        items=items,
        page=page,
        limit=limit,
        total=total,
        query=q,
    )


# =========================================================
# GET /routines/{routine_id}
# =========================================================

@router.get(
    "/{routine_id}",
    response_model=RoutineDetailResponse,
)
@user_exist
async def get_routine(
    routine_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await get_routine_service(
        db=db,
        user_id=_user_id(current_user),
        routine_id=routine_id,
    )


# =========================================================
# POST /routines
# =========================================================

@router.post(
    "/",
    response_model=RoutineDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
@user_exist
async def create_routine(
    request: CreateRoutineRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await create_routine_service(
        db=db,
        user_id=_user_id(current_user),
        request=request,
    )

    # -------------------------------------------------------
    # Invalidate cache
    # -------------------------------------------------------
    # A new routine changes what /routines (list/search) and
    # any future GET /routines/{id} for this id should return.
    # This runs only after create_routine_service has
    # successfully committed.

    await invalidate_routine()

    return result


# =========================================================
# PUT /routines/{routine_id}
# =========================================================

@router.put(
    "/{routine_id}",
    response_model=RoutineDetailResponse,
)
@user_exist
async def update_routine(
    routine_id: int,
    request: UpdateRoutineRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await update_routine_service(
        db=db,
        user_id=_user_id(current_user),
        routine_id=routine_id,
        request=request,
    )

    # -------------------------------------------------------
    # Invalidate cache
    # -------------------------------------------------------
    # Bumps the ROUTINES namespace version, so the old
    # cached detail/list/search entries for this routine
    # are no longer reachable (old keys just expire naturally
    # via TTL instead of being actively deleted).

    await invalidate_routine()

    return result


# =========================================================
# DELETE /routines/{routine_id}
# =========================================================

@router.delete(
    "/{routine_id}",
    response_model=DeleteRoutineResponse,
)
@user_exist
async def delete_routine(
    routine_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    await delete_routine_service(
        db=db,
        user_id=_user_id(current_user),
        routine_id=routine_id,
    )

    # -------------------------------------------------------
    # Invalidate cache
    # -------------------------------------------------------
    # Prevents a deleted routine from still being served out
    # of Redis for up to ROUTINE_CACHE_TTL seconds.

    await invalidate_routine()

    return DeleteRoutineResponse(
        message="Routine deleted successfully",
    )