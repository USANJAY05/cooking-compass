from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator

from .components_schema import (
    IngredientComponent,
    InstructionComponent,
)


# ---------------------------------------------------------
# GET /recipes
# ---------------------------------------------------------

class GetRecipesRequest(BaseModel):
    scope: Literal["mine", "public"] = "public"

    category_id: int | None = Field(
        default=None,
        gt=0,
    )

    tag_id: int | None = Field(
        default=None,
        gt=0,
    )

    user_id: int | None = Field(
        default=None,
        gt=0,
    )

    page: int = Field(
        default=1,
        ge=1,
    )

    limit: int = Field(
        default=20,
        ge=1,
        le=100,
    )

    sort_by: Literal[
        "created_at",
        "name",
        "rating",
        "cooking_time",
    ] = "created_at"

    sort_order: Literal["asc", "desc"] = "desc"


# ---------------------------------------------------------
# GET /recipes/search
# ---------------------------------------------------------

class SearchRecipesRequest(BaseModel):
    q: str = Field(
        min_length=1,
        max_length=255,
    )

    scope: Literal["mine", "public"] = "public"

    category_id: int | None = Field(
        default=None,
        gt=0,
    )

    tag_id: int | None = Field(
        default=None,
        gt=0,
    )

    page: int = Field(
        default=1,
        ge=1,
    )

    limit: int = Field(
        default=20,
        ge=1,
        le=100,
    )

    sort_by: Literal[
        "created_at",
        "name",
        "rating",
        "cooking_time",
    ] = "created_at"

    sort_order: Literal["asc", "desc"] = "desc"


# ---------------------------------------------------------
# POST /recipes
# ---------------------------------------------------------

class CreateRecipeRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    preparation_time: int = Field(
        ge=0,
    )

    cooking_time: int = Field(
        ge=0,
    )

    total_time: int = Field(
        ge=0,
    )

    servings: int = Field(
        ge=1,
        le=1000,
    )

    visibility: Literal["PRIVATE", "PUBLIC"] = "PRIVATE"

    image_urls: list[HttpUrl] = Field(
        default_factory=list,
        max_length=10,
    )

    ingredients: list[IngredientComponent] = Field(
        min_length=1,
        max_length=100,
    )

    instructions: list[InstructionComponent] = Field(
        min_length=1,
        max_length=100,
    )

    category_ids: list[int] = Field(
        default_factory=list,
        max_length=20,
    )

    tag_ids: list[int] = Field(
        default_factory=list,
        max_length=50,
    )

    @field_validator("category_ids", "tag_ids")
    @classmethod
    def validate_ids(cls, value: list[int]) -> list[int]:
        if any(item <= 0 for item in value):
            raise ValueError("IDs must be greater than 0")

        if len(value) != len(set(value)):
            raise ValueError("Duplicate IDs are not allowed")

        return value


# ---------------------------------------------------------
# PUT /recipes/{recipe_id}
# ---------------------------------------------------------

class UpdateRecipeRequest(CreateRecipeRequest):
    pass


# ---------------------------------------------------------
# POST /recipes/{recipe_id}/rating
# ---------------------------------------------------------

class CreateOrUpdateRatingRequest(BaseModel):
    rating: int = Field(
        ge=1,
        le=5,
    )

    review: str | None = Field(
        default=None,
        max_length=5000,
    )