from typing import Literal

from fastapi import APIRouter, Depends, Path, Query, status

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

from cooking_compass.service.recipe.create_recipe import (
    create_recipe_service,
)

from cooking_compass.service.recipe.get_recipes import (
    get_recipes_service,
)

from cooking_compass.service.recipe.get_recipe_by_id import (
    get_recipe_by_id_service,
)
from src.cooking_compass.service.recipe.create_recipe import create_recipe_service


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
async def get_recipes(
    scope: Literal["mine", "public"] = Query(
        default="public",
        description="Recipe scope: mine or public",
    ),
    category_id: int | None = Query(
        default=None,
        gt=0,
    ),
    tag_id: int | None = Query(
        default=None,
        gt=0,
    ),
    user_id: int | None = Query(
        default=None,
        gt=0,
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
    sort_by: Literal[
        "created_at",
        "name",
        "rating",
        "cooking_time",
    ] = Query(
        default="created_at",
    ),
    sort_order: Literal[
        "asc",
        "desc",
    ] = Query(
        default="desc",
    ),
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
async def search_recipes(
    q: str = Query(
        ...,
        min_length=1,
        max_length=255,
    ),
    scope: Literal["mine", "public"] = Query(
        default="public",
        description="Recipe scope: mine or public",
    ),
    category_id: int | None = Query(
        default=None,
        gt=0,
    ),
    tag_id: int | None = Query(
        default=None,
        gt=0,
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
    sort_by: Literal[
        "created_at",
        "name",
        "rating",
        "cooking_time",
    ] = Query(
        default="created_at",
    ),
    sort_order: Literal[
        "asc",
        "desc",
    ] = Query(
        default="desc",
    ),
    current_user: dict = Depends(ensure_user_exists),
):
    return "search recipes"


# =========================================================
# GET /recipes/{recipe_id}
# Get a single recipe
# =========================================================
@router.get(
    "/{recipe_id}",
    response_model=RecipeDetailResponse,
)
async def get_recipe(
    recipe_id: int = Path(
        ...,
        gt=0,
    ),
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
async def update_recipe(
    recipe_id: int = Path(
        ...,
        gt=0,
    ),
    request: UpdateRecipeRequest = None,
    current_user: dict = Depends(ensure_user_exists),
):
    return "update recipe"


# =========================================================
# DELETE /recipes/{recipe_id}
# Soft delete recipe
# =========================================================
@router.delete(
    "/{recipe_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_recipe(
    recipe_id: int = Path(
        ...,
        gt=0,
    ),
    current_user: dict = Depends(ensure_user_exists),
):
    return None


# =========================================================
# POST /recipes/{recipe_id}/rating
# Create or update user's rating/review
# =========================================================
@router.post(
    "/{recipe_id}/rating",
    response_model=RatingResponse,
)
async def create_or_update_rating(
    recipe_id: int = Path(
        ...,
        gt=0,
    ),
    request: CreateOrUpdateRatingRequest = None,
    current_user: dict = Depends(ensure_user_exists),
):
    return "create or update rating"


# =========================================================
# DELETE /recipes/{recipe_id}/rating
# Delete user's rating/review
# =========================================================
@router.delete(
    "/{recipe_id}/rating",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_rating(
    recipe_id: int = Path(
        ...,
        gt=0,
    ),
    current_user: dict = Depends(ensure_user_exists),
):
    return None