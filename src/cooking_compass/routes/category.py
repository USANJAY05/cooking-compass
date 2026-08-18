from fastapi import APIRouter, Depends, Query, status

from cooking_compass.schema.category.request_schema import (
    CreateCategoryRequest,
    UpdateCategoryRequest,
)

from cooking_compass.service.category.create_category import (
    create_category_service,
)
from cooking_compass.service.category.list_categories import (
    list_categories_service,
)
from cooking_compass.service.category.search_category import (
    search_categories_service,
)
from cooking_compass.service.category.update_category import (
    update_category_service,
)
from cooking_compass.service.category.delete_category import (
    delete_category_service,
)

from cooking_compass.utils.ensure_user import ensure_user_exists
from cooking_compass.utils.require_admin import require_admin


router = APIRouter(
    prefix="/categories",
    tags=["CATEGORIES"],
)


# GET ALL CATEGORIES WITH PAGINATION
@router.get("/")
async def list_categories(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(ensure_user_exists),
):
    return await list_categories_service(
        page,
        page_size,
    )


# SEARCH CATEGORIES
@router.get("/search")
async def search_categories(
    q: str = Query(..., min_length=1, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(ensure_user_exists),
):
    return await search_categories_service(
        q,
        page,
        page_size,
    )


# CREATE CATEGORY
@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    request: CreateCategoryRequest,
    current_user: dict = Depends(require_admin),
):
    return await create_category_service(request)


# UPDATE CATEGORY
@router.put("/{category_id}")
async def update_category(
    category_id: int,
    request: UpdateCategoryRequest,
    current_user: dict = Depends(require_admin),
):
    return await update_category_service(
        category_id,
        request,
    )


# DELETE CATEGORY
@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_category(
    category_id: int,
    current_user: dict = Depends(require_admin),
):
    return await delete_category_service(category_id)