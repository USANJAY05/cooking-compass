from fastapi import APIRouter, Depends, status

from cooking_compass.schema.ingredient.request_schema import (
    CreateIngredientRequest,
    UpdateIngredientRequest,
)
from cooking_compass.service.ingredient.ingredient_service import (
    list_ingredients_service,
    create_ingredient_service,
    update_ingredient_service,
    delete_ingredient_service,
)
from cooking_compass.utils.ensure_user import ensure_user_exists
from cooking_compass.utils.require_admin import require_admin

router = APIRouter(prefix="/ingredients", tags=["INGREDIENTS"])


@router.get("/")
async def list_ingredients(current_user: dict = Depends(ensure_user_exists)):
    return await list_ingredients_service()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_ingredient(
    request: CreateIngredientRequest,
    current_user: dict = Depends(require_admin),
):
    return await create_ingredient_service(request)


@router.put("/{ingredient_id}")
async def update_ingredient(
    ingredient_id: int,
    request: UpdateIngredientRequest,
    current_user: dict = Depends(require_admin),
):
    return await update_ingredient_service(ingredient_id, request)


@router.delete("/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ingredient(
    ingredient_id: int,
    current_user: dict = Depends(require_admin),
):
    return await delete_ingredient_service(ingredient_id)