from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RoutineRecipeComponent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recipe_id: int = Field(gt=0)
    recipe_name: str = Field(
        min_length=1,
        max_length=255,
    )
    recipe_thumbnail_url: str | None = None

    meal_type: Literal[
        "BREAKFAST",
        "LUNCH",
        "DINNER",
        "SNACK",
    ]

    day_of_week: int = Field(
        ge=1,
        le=7,
    )

    servings: int = Field(
        ge=1,
        le=1000,
    )


class RecurrenceComponent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    frequency: Literal[
        "DAILY",
        "WEEKLY",
    ]

    interval: int = Field(
        default=1,
        ge=1,
    )

    days_of_week: list[int] = Field(
        default_factory=list,
        max_length=7,
    )

    start_date: date
    end_date: date | None = None


class RoutineSummaryComponent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    start_date: date
    end_date: date | None