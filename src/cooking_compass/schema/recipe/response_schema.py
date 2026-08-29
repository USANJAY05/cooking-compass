from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
)

from cooking_compass.schema.recipe.components_schema import (
    CookedWeightUnit,
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

    servings: int | None

    visibility: str

    cooked_weight_amount: float | None = Field(
        default=None,
        gt=0,
        description="Weight/volume of the finished, cooked dish",
    )

    cooked_weight_unit: CookedWeightUnit | None = Field(
        default=None,
        description="Unit for cooked_weight_amount: g, kg, oz, l, or ml",
    )


class RecipeDetailResponse(RecipeBaseResponse):
    image_urls: list[HttpUrl] = Field(
        default_factory=list,
    )

    ingredients: list[IngredientComponent] = Field(
        default_factory=list,
    )

    instructions: list[InstructionComponent] = Field(
        default_factory=list,
    )

    category_ids: list[int] = Field(
        default_factory=list,
    )

    tag_ids: list[int] = Field(
        default_factory=list,
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