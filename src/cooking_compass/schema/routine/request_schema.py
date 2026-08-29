from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from cooking_compass.schema.routine.components_schema import (
    RecurrenceComponent,
    RoutineItemRequest,
)


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
    ] = "created_at"

    sort_order: Literal[
        "asc",
        "desc",
    ] = "desc"


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
    ] = "created_at"

    sort_order: Literal[
        "asc",
        "desc",
    ] = "desc"


class CreateRoutineRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    items: list[RoutineItemRequest] = Field(
        min_length=1,
        max_length=100,
    )

    recurrence: RecurrenceComponent

    @field_validator("items")
    @classmethod
    def validate_items(
        cls,
        value: list[RoutineItemRequest],
    ) -> list[RoutineItemRequest]:

        recipe_ids = [
            item.recipe_id
            for item in value
        ]

        if len(recipe_ids) != len(set(recipe_ids)):
            raise ValueError(
                "Duplicate recipe IDs are not allowed"
            )

        return value

    @field_validator("recurrence")
    @classmethod
    def validate_recurrence(
        cls,
        value: RecurrenceComponent,
    ) -> RecurrenceComponent:

        if (
            value.end_date is not None
            and value.end_date < value.start_date
        ):
            raise ValueError(
                "Recurrence end date cannot be before start date"
            )

        if value.frequency != "WEEKLY":
            value.days_of_week = []

        return value


class UpdateRoutineRequest(CreateRoutineRequest):
    pass