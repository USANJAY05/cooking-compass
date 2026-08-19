from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from .components_schema import (
    IngredientComponent,
    InstructionComponent,
    NutritionComponent,
    RatingComponent,
    RecipeSummaryComponent,
)


class RecipeBaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    preparation_time: int
    cooking_time: int
    total_time: int
    servings: int
    visibility: str


# class RecipeDetailResponse(RecipeBaseResponse):
#     image_urls: list[HttpUrl] = Field(default_factory=list)

#     ingredients: list[IngredientComponent] = Field(
#         default_factory=list
#     )

#     instructions: list[InstructionComponent] = Field(
#         default_factory=list
#     )

#     category_ids: list[int] = Field(
#         default_factory=list
#     )

#     tag_ids: list[int] = Field(
#         default_factory=list
#     )

class RecipeDetailResponse(RecipeBaseResponse):
    image_urls: list[HttpUrl] = Field(default_factory=list)

    ingredients: list[IngredientComponent] = Field(
        default_factory=list
    )

    instructions: list[InstructionComponent] = Field(
        default_factory=list
    )

    category_ids: list[int] = Field(
        default_factory=list
    )

    tag_ids: list[int] = Field(
        default_factory=list
    )

    nutrition: NutritionComponent | None = None

    rating: RatingComponent | None = None

    
class RecipeListResponse(BaseModel):
    items: list[RecipeSummaryComponent]

    page: int
    limit: int
    total: int


class RecipeSearchResponse(RecipeListResponse):
    query: str


class RatingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recipe_id: int
    rating: int
    review: str | None


class DeleteRecipeResponse(BaseModel):
    message: str