from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from .components_schema import RecurrenceComponent


# ---------------------------------------------------------
# GET /routines
# ---------------------------------------------------------

class GetRoutinesRequest(BaseModel):
    scope: Literal["mine", "feed"] = "mine"

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
        "start_date",
    ] = "created_at"

    sort_order: Literal[
        "asc",
        "desc",
    ] = "desc"


# ---------------------------------------------------------
# GET /routines/search
# ---------------------------------------------------------

class SearchRoutinesRequest(BaseModel):
    q: str = Field(
        min_length=1,
        max_length=255,
    )

    scope: Literal["mine", "feed"] = "mine"

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
        "start_date",
    ] = "created_at"

    sort_order: Literal[
        "asc",
        "desc",
    ] = "desc"


# ---------------------------------------------------------
# POST /routines
# ---------------------------------------------------------

class CreateRoutineRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    start_date: date

    end_date: date | None = None

    recipe_ids: list[int] = Field(
        min_length=1,
        max_length=100,
    )

    recurrence: RecurrenceComponent | None = None

    @field_validator("recipe_ids")
    @classmethod
    def validate_recipe_ids(
        cls,
        value: list[int],
    ) -> list[int]:
        if any(recipe_id <= 0 for recipe_id in value):
            raise ValueError(
                "Recipe IDs must be greater than 0"
            )

        if len(value) != len(set(value)):
            raise ValueError(
                "Duplicate recipe IDs are not allowed"
            )

        return value

    @field_validator("end_date")
    @classmethod
    def validate_end_date(
        cls,
        value: date | None,
        info,
    ) -> date | None:
        start_date = info.data.get("start_date")

        if value is not None and start_date is not None:
            if value < start_date:
                raise ValueError(
                    "End date cannot be before start date"
                )

        return value


# ---------------------------------------------------------
# PUT /routines/{routine_id}
# ---------------------------------------------------------

class UpdateRoutineRequest(CreateRoutineRequest):
    pass