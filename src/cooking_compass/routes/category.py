from fastapi import APIRouter, Depends, status

from cooking_compass.schema.category.request_schema import (
    CreateCategoryRequest,
    UpdateCategoryRequest,
)
from cooking_compass.service.category.category_service import (
    list_categories_service,
    create_category_service,
    update_category_service,
    delete_category_service,
)
from cooking_compass.utils.ensure_user import ensure_user_exists
from cooking_compass.utils.require_admin import require_admin

router = APIRouter(prefix="/categories", tags=["CATEGORIES"])


@router.get("/")
async def list_categories(current_user: dict = Depends(ensure_user_exists)):
    return await list_categories_service()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_category(
    request: CreateCategoryRequest,
    current_user: dict = Depends(require_admin),
):
    return await create_category_service(request)


@router.put("/{category_id}")
async def update_category(
    category_id: int,
    request: UpdateCategoryRequest,
    current_user: dict = Depends(require_admin),
):
    return await update_category_service(category_id, request)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    current_user: dict = Depends(require_admin),
):
    return await delete_category_service(category_id)