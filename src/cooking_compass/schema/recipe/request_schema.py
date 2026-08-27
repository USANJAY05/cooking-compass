from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

from cooking_compass.schema.recipe.components_schema import (
    CookedWeightUnit,
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

    # Now optional — not every recipe has a well-defined serving count
    # (e.g. a sauce, a spice blend, a "makes as much as you like" recipe).
    servings: int | None = Field(
        default=None,
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

    tag_names: list[str] = Field(
        default_factory=list,
        max_length=50,
    )

    cooked_weight_amount: float | None = Field(
        default=None,
        gt=0,
        description="Weight/volume of the finished, cooked dish",
    )

    cooked_weight_unit: CookedWeightUnit | None = Field(
        default=None,
        description="Unit for cooked_weight_amount: g, kg, oz, l, or ml",
    )

    @field_validator("category_ids")
    @classmethod
    def validate_category_ids(cls, value: list[int]) -> list[int]:
        if any(item <= 0 for item in value):
            raise ValueError("IDs must be greater than 0")

        if len(value) != len(set(value)):
            raise ValueError("Duplicate IDs are not allowed")

        return value

    @field_validator("tag_names")
    @classmethod
    def validate_tag_names(cls, value: list[str]) -> list[str]:
        cleaned = [name.strip() for name in value]

        if any(not name for name in cleaned):
            raise ValueError("Tag names must not be empty")

        if any(len(name) > 50 for name in cleaned):
            raise ValueError("Tag names must be 50 characters or fewer")

        lowered = [name.lower() for name in cleaned]
        if len(lowered) != len(set(lowered)):
            raise ValueError("Duplicate tag names are not allowed")

        return cleaned

    @model_validator(mode="after")
    def validate_cooked_weight_pair(self):
        has_amount = self.cooked_weight_amount is not None
        has_unit = self.cooked_weight_unit is not None

        if has_amount != has_unit:
            raise ValueError(
                "cooked_weight_amount and cooked_weight_unit must be "
                "provided together"
            )

        return self


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