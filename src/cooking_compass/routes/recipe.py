from typing import Literal

from fastapi import APIRouter, Depends, Query, status, HTTPException, Path

from cooking_compass.utils.ensure_user import ensure_user_exists
from cooking_compass.utils.check_user_exist import user_exist

from cooking_compass.schema.recipe.request_schema import (
    CreateOrUpdateRatingRequest,
    CreateRecipeRequest,
    UpdateRecipeRequest,
)

from cooking_compass.schema.recipe.response_schema import (
    DeleteRecipeResponse,
    RatingResponse,
    RecipeDetailResponse,
    RecipeListResponse,
    RecipeSearchResponse,
)

from cooking_compass.service.recipe.create_recipe import create_recipe_service
from cooking_compass.service.recipe.get_recipes import get_recipes_service
from cooking_compass.service.recipe.get_recipe_by_id import get_recipe_by_id_service
from cooking_compass.service.recipe.search_recipes import search_recipes_service
from cooking_compass.service.recipe.delete_recipe import delete_recipe_service
from cooking_compass.service.recipe.update_recipe import update_recipe_service
from cooking_compass.service.recipe.ratings.ratings_recipe import (
    create_or_update_rating_service,
)
from cooking_compass.service.recipe.ratings.delete_rating import (
    delete_rating_service,
)

router = APIRouter(
    prefix="/recipes",
    tags=["RECIPES"],
)


# =========================================================
# GET /recipes
# Get recipes with pagination, filters and sorting
# =========================================================
@router.get(
    "/",
    response_model=RecipeListResponse,
)
@user_exist
async def get_recipes(
    scope: Literal["mine", "public"] = Query(
        default="public",
        description="Recipe scope: mine or public",
    ),
    category_id: int | None = Query(default=None, gt=0),
    tag_id: int | None = Query(default=None, gt=0),
    user_id: int | None = Query(default=None, gt=0),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    sort_by: Literal[
        "created_at", "name", "rating", "cooking_time",
    ] = Query(default="created_at"),
    sort_order: Literal["asc", "desc"] = Query(default="desc"),
    current_user: dict = Depends(ensure_user_exists),
):
    return await get_recipes_service(
        scope=scope,
        category_id=category_id,
        tag_id=tag_id,
        user_id=user_id,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        current_user=current_user,
    )


# =========================================================
# GET /recipes/search
# Search recipes
# =========================================================
@router.get(
    "/search",
    response_model=RecipeSearchResponse,
)
@user_exist
async def search_recipes(
    q: str = Query(..., min_length=1, max_length=255),
    scope: Literal["mine", "public"] = Query(
        default="public",
        description="Recipe scope: mine or public",
    ),
    category_id: int | None = Query(default=None, gt=0),
    tag_id: int | None = Query(default=None, gt=0),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    sort_by: Literal[
        "created_at", "name", "rating", "cooking_time",
    ] = Query(default="created_at"),
    sort_order: Literal["asc", "desc"] = Query(default="desc"),
    current_user: dict = Depends(ensure_user_exists),
):
    return await search_recipes_service(
        current_user=current_user,
        q=q,
        scope=scope,
        category_id=category_id,
        tag_id=tag_id,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )


# =========================================================
# GET /recipes/{recipe_id}
# Get a single recipe
# =========================================================
@router.get(
    "/{recipe_id}",
    response_model=RecipeDetailResponse,
)
@user_exist
async def get_recipe(
    recipe_id: int = Path(..., gt=0),
    current_user: dict = Depends(ensure_user_exists),
):
    return await get_recipe_by_id_service(
        recipe_id=recipe_id,
        current_user=current_user,
    )


# =========================================================
# POST /recipes
# Create recipe
# =========================================================
@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
)
@user_exist
async def create_recipe(
    request: CreateRecipeRequest,
    current_user: dict = Depends(ensure_user_exists),
):
    return await create_recipe_service(
        request,
        current_user,
    )


# =========================================================
# PUT /recipes/{recipe_id}
# Update recipe
# =========================================================
@router.put(
    "/{recipe_id}",
    response_model=RecipeDetailResponse,
)
@user_exist
async def update_recipe(
    recipe_id: int = Path(..., gt=0),
    request: UpdateRecipeRequest = None,
    current_user: dict = Depends(ensure_user_exists),
):
    return await update_recipe_service(recipe_id, request, current_user)


# =========================================================
# DELETE /recipes/{recipe_id}
# Soft delete recipe
# =========================================================
@router.delete(
    "/{recipe_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@user_exist
async def delete_recipe(
    recipe_id: int = Path(..., gt=0),
    current_user: dict = Depends(ensure_user_exists),
):
    deleted = await delete_recipe_service(
        recipe_id=recipe_id,
        current_user=current_user,
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found",
        )
    return None


# =========================================================
# POST /recipes/{recipe_id}/rating
# Create or update user's rating/review
# =========================================================
@router.post(
    "/{recipe_id}/rating",
    response_model=RatingResponse,
)
@user_exist
async def create_or_update_rating(
    recipe_id: int = Path(..., gt=0),
    request: CreateOrUpdateRatingRequest = None,
    current_user: dict = Depends(ensure_user_exists),
):
    return await create_or_update_rating_service(recipe_id, request, current_user)


# =========================================================
# DELETE /recipes/{recipe_id}/rating
# Delete user's rating/review
# =========================================================
@router.delete(
    "/{recipe_id}/rating",
    status_code=status.HTTP_204_NO_CONTENT,
)
@user_exist
async def delete_rating(
    recipe_id: int = Path(..., gt=0),
    current_user: dict = Depends(ensure_user_exists),
):
    deleted = await delete_rating_service(
        recipe_id=recipe_id,
        current_user=current_user,
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rating not found",
        )
    return None