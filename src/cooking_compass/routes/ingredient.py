from fastapi import APIRouter, Depends, Query, status

from cooking_compass.schema.ingredient.request_schema import (
    CreateIngredientRequest,
    UpdateIngredientRequest,
)

from cooking_compass.service.ingredient.create_ingredient import (
    create_ingredient_service,
)
from cooking_compass.service.ingredient.list_ingredients import (
    list_ingredients_service,
)
from cooking_compass.service.ingredient.search_ingredient import (
    search_ingredients_service,
)
from cooking_compass.service.ingredient.update_ingredient import (
    update_ingredient_service,
)
from cooking_compass.service.ingredient.delete_ingredient import (
    delete_ingredient_service,
)

from cooking_compass.utils.ensure_user import ensure_user_exists
from cooking_compass.utils.require_admin import require_admin


router = APIRouter(
    prefix="/ingredients",
    tags=["INGREDIENTS"],
)


# GET ALL INGREDIENTS WITH PAGINATION
@router.get("/")
async def list_ingredients(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(ensure_user_exists),
):
    return await list_ingredients_service(
        page,
        page_size,
    )


# SEARCH INGREDIENTS
@router.get("/search")
async def search_ingredients(
    q: str = Query(..., min_length=1, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(ensure_user_exists),
):
    return await search_ingredients_service(
        q,
        page,
        page_size,
    )


# CREATE INGREDIENT
@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
)
async def create_ingredient(
    request: CreateIngredientRequest,
    current_user: dict = Depends(require_admin),
):
    return await create_ingredient_service(request)


# UPDATE INGREDIENT
@router.put("/{ingredient_id}")
async def update_ingredient(
    ingredient_id: int,
    request: UpdateIngredientRequest,
    current_user: dict = Depends(require_admin),
):
    return await update_ingredient_service(
        ingredient_id,
        request,
    )


# DELETE INGREDIENT
@router.delete(
    "/{ingredient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_ingredient(
    ingredient_id: int,
    current_user: dict = Depends(require_admin),
):
    return await delete_ingredient_service(ingredient_id)