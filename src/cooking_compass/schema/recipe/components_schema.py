from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class CookedWeightUnit(str, Enum):
    GRAM = "g"
    KILOGRAM = "kg"
    OUNCE = "oz"
    LITER = "l"
    MILLILITER = "ml"


# Conversion factor to grams.
# NOTE: liter/ml are volume units, not mass. We convert them assuming a
# density of ~1 g/ml (water-like), which is a standard simplification for
# home-cooking apps.
_TO_GRAMS: dict[CookedWeightUnit, float] = {
    CookedWeightUnit.GRAM: 1.0,
    CookedWeightUnit.KILOGRAM: 1000.0,
    CookedWeightUnit.OUNCE: 28.349523125,
    CookedWeightUnit.LITER: 1000.0,
    CookedWeightUnit.MILLILITER: 1.0,
}


def to_grams(
    amount: float,
    unit: "CookedWeightUnit | str",
) -> float:
    """Convert a cooked-weight amount in any supported unit to grams."""

    unit = CookedWeightUnit(unit)

    return round(
        amount * _TO_GRAMS[unit],
        2,
    )


# ============================================================
# Ingredient
# ============================================================


class IngredientComponent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ingredient_id: int = Field(
        gt=0,
    )

    name: str = Field(
        min_length=1,
        max_length=200,
    )

    quantity: float = Field(
        gt=0,
    )

    unit: str = Field(
        min_length=1,
        max_length=50,
    )

    display_order: int = Field(
        default=1,
        ge=1,
    )


# ============================================================
# Instruction
# ============================================================


class InstructionComponent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    step_number: int = Field(
        ge=1,
    )

    instruction_text: str = Field(
        min_length=1,
        max_length=5000,
    )

    timer_seconds: int | None = Field(
        default=None,
        ge=0,
    )

    tip: str | None = Field(
        default=None,
        max_length=1000,
    )

    reference_recipe_id: int | None = Field(
        default=None,
        gt=0,
    )

    reference_image: str | None = None


# ============================================================
# Nutrition
# ============================================================


class NutritionType(str, Enum):
    MACRO = "macro"
    MICRO = "micro"
    OTHER = "other"


class NutritionItemComponent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str = Field(
        min_length=1,
        max_length=50,
    )

    name: str = Field(
        min_length=1,
        max_length=100,
    )

    amount: float = Field(
        ge=0,
    )

    unit: str = Field(
        min_length=1,
        max_length=30,
    )

    type: NutritionType


class NutritionComponent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    servings: int = Field(
        ge=1,
    )

    items: list[NutritionItemComponent] = Field(
        default_factory=list,
    )


# ============================================================
# Rating
# ============================================================


class RatingComponent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    average: float = Field(
        ge=0,
        le=5,
    )

    count: int = Field(
        ge=0,
    )


# ============================================================
# Recipe Summary
# ============================================================


class RecipeSummaryComponent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(
        gt=0,
    )

    name: str = Field(
        min_length=1,
        max_length=255,
    )

    thumbnail_url: str | None = None

    preparation_time: int | None = Field(
        default=None,
        ge=0,
    )

    cooking_time: int | None = Field(
        default=None,
        ge=0,
    )

    servings: int | None = Field(
        default=None,
        ge=1,
    )

    rating: RatingComponent