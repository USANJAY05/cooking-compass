from pydantic import BaseModel, ConfigDict, Field


class IngredientComponent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ingredient_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=200)
    quantity: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=50)
    display_order: int = Field(default=1, ge=1)

class InstructionComponent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    step_number: int = Field(ge=1)
    instruction_text: str = Field(min_length=1, max_length=5000)
    timer_seconds: int | None = Field(default=None, ge=0)
    tip: str | None = Field(default=None, max_length=1000)
    reference_recipe_id: int | None = Field(default=None, gt=0)
    reference_image: str | None = Field(default=None)

class NutritionItemComponent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=100)
    amount: float = Field(ge=0)
    unit: str = Field(min_length=1, max_length=30)

class NutritionComponent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    servings: int = Field(ge=1)
    items: list[NutritionItemComponent] = Field(default_factory=list)


class RatingComponent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    average: float = Field(ge=0, le=5)
    count: int = Field(ge=0)


class RecipeSummaryComponent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=255)
    thumbnail_url: str | None = None
    preparation_time: int | None = Field(default=None, ge=0)
    cooking_time: int | None = Field(default=None, ge=0)
    servings: int = Field(ge=1)
    rating: RatingComponent