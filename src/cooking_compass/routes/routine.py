from fastapi import APIRouter, Depends, Query, status

from cooking_compass.auth.keycloak import get_current_user

from cooking_compass.schema.routine.request_schema import (
    CreateRoutineRequest,
    UpdateRoutineRequest,
)

from cooking_compass.schema.routine.response_schema import (
    RoutineDetailResponse,
    RoutineListResponse,
    RoutineSearchResponse,
)


router = APIRouter(
    prefix="/routines",
    tags=["ROUTINES"],
)


# ---------------------------------------------------------
# GET /routines
# Get routines
# ---------------------------------------------------------
@router.get(
    "/",
    response_model=RoutineListResponse,
)
def get_routines(
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
    current_user: dict = Depends(get_current_user),
):
    return "get routines"


# ---------------------------------------------------------
# GET /routines/search
# Search routines
# ---------------------------------------------------------
@router.get(
    "/search",
    response_model=RoutineSearchResponse,
)
def search_routines(
    q: str = Query(
        ...,
        min_length=1,
        max_length=255,
    ),
    scope: str = Query(
        default="mine",
        description="Search scope: mine or feed",
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
    current_user: dict = Depends(get_current_user),
):
    return "search routines"


# ---------------------------------------------------------
# GET /routines/{routine_id}
# Get a specific routine
# ---------------------------------------------------------
@router.get(
    "/{routine_id}",
    response_model=RoutineDetailResponse,
)
def get_routine(
    routine_id: int,
    current_user: dict = Depends(get_current_user),
):
    return "get routine"


# ---------------------------------------------------------
# POST /routines
# Create routine
# ---------------------------------------------------------
@router.post(
    "/",
    response_model=RoutineDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_routine(
    request: CreateRoutineRequest,
    current_user: dict = Depends(get_current_user),
):
    return "create routine"


# ---------------------------------------------------------
# PUT /routines/{routine_id}
# Update routine
# ---------------------------------------------------------
@router.put(
    "/{routine_id}",
    response_model=RoutineDetailResponse,
)
def update_routine(
    routine_id: int,
    request: UpdateRoutineRequest,
    current_user: dict = Depends(get_current_user),
):
    return "update routine"


# ---------------------------------------------------------
# DELETE /routines/{routine_id}
# Soft delete routine
# ---------------------------------------------------------
@router.delete(
    "/{routine_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_routine(
    routine_id: int,
    current_user: dict = Depends(get_current_user),
):
    return None