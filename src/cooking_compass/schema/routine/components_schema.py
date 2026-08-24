from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# =========================================================
# ROUTINE ITEM
# =========================================================

class RoutineItemComponent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recipe_id: int = Field(gt=0)

    recipe_name: str = Field(
        min_length=1,
        max_length=255,
    )

    recipe_thumbnail_url: str | None = None

    quantity: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=2,
    )

    quantity_unit: Literal[
        "SERVING",
        "G",
        "KG",
        "ML",
        "L",
    ]

class RoutineItemRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recipe_id: int = Field(gt=0)

    quantity: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=2,
    )

    quantity_unit: Literal[
        "SERVING",
        "G",
        "KG",
        "ML",
        "L",
    ]

# =========================================================
# RECURRENCE
# =========================================================

class RecurrenceComponent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    frequency: Literal[
        "DAILY",
        "WEEKLY",
        "MONTHLY",
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

    occurrence_count: int | None = Field(
        default=None,
        ge=1,
    )

    @field_validator("days_of_week", mode="before")
    @classmethod
    def parse_days_of_week(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            if not value.strip():
                return []
            return [int(day) for day in value.split(",")]
        return value


# =========================================================
# ROUTINE SUMMARY
# =========================================================

class RoutineSummaryComponent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int

    name: str

    description: str | None

    created_at: datetime | None = None

    updated_at: datetime | None = None
