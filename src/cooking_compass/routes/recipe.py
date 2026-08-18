from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from cooking_compass.utils.ensure_user import ensure_user_exists

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

from src.cooking_compass.service.recipe.create_recipe import create_recipe_service

from cooking_compass.utils.check_user_exist import user_exist

router = APIRouter(
    prefix="/recipes",
    tags=["RECIPES"],
)


# ---------------------------------------------------------
# GET /recipes
# Get recipes
# ---------------------------------------------------------
@router.get(
    "/",
    response_model=RecipeListResponse,
)
def get_recipes(
    scope: str = Query(
        default="public",
        description="Recipe scope: mine or public",
    ),
    category_id: Optional[int] = Query(default=None),
    tag_id: Optional[int] = Query(default=None),
    user_id: Optional[int] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    current_user: dict = Depends(ensure_user_exists),
):
    return "get recipes"


# ---------------------------------------------------------
# GET /recipes/search
# Search recipes
# ---------------------------------------------------------
@router.get(
    "/search",
    response_model=RecipeSearchResponse,
)
def search_recipes(
    q: str = Query(..., min_length=1),
    scope: str = Query(
        default="public",
        description="Search scope: mine or public",
    ),
    category_id: Optional[int] = Query(default=None),
    tag_id: Optional[int] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    current_user: dict = Depends(ensure_user_exists),
):
    return "search recipes"


# ---------------------------------------------------------
# GET /recipes/{recipe_id}
# Get a single recipe
# ---------------------------------------------------------
@router.get(
    "/{recipe_id}",
    response_model=RecipeDetailResponse,
)
def get_recipe(
    recipe_id: int,
    current_user: dict = Depends(ensure_user_exists),
):
    return "get recipe"


# ---------------------------------------------------------
# POST /recipes
# Create recipe
# ---------------------------------------------------------
@router.post(
    "/",
    # response_model=RecipeDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
@user_exist
async def create_recipe(
    request: CreateRecipeRequest,
    current_user: dict = Depends(ensure_user_exists),
):
    
    return await create_recipe_service(request, current_user)


# ---------------------------------------------------------
# PUT /recipes/{recipe_id}
# Update recipe
# ---------------------------------------------------------
@router.put(
    "/{recipe_id}",
    response_model=RecipeDetailResponse,
)
def update_recipe(
    recipe_id: int,
    request: UpdateRecipeRequest,
    current_user: dict = Depends(ensure_user_exists),
):
    return "update recipe"


# ---------------------------------------------------------
# DELETE /recipes/{recipe_id}
# Soft delete recipe
# ---------------------------------------------------------
@router.delete(
    "/{recipe_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_recipe(
    recipe_id: int,
    current_user: dict = Depends(ensure_user_exists),
):
    return None


# ---------------------------------------------------------
# POST /recipes/{recipe_id}/rating
# Create or update user's rating/review
# ---------------------------------------------------------
@router.post(
    "/{recipe_id}/rating",
    response_model=RatingResponse,
)
def create_or_update_rating(
    recipe_id: int,
    request: CreateOrUpdateRatingRequest,
    current_user: dict = Depends(ensure_user_exists),
):
    return "create or update rating"


# ---------------------------------------------------------
# DELETE /recipes/{recipe_id}/rating
# Delete user's rating/review
# ---------------------------------------------------------
@router.delete(
    "/{recipe_id}/rating",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_rating(
    recipe_id: int,
    current_user: dict = Depends(ensure_user_exists),
):
    return None