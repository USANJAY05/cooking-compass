from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from .components_schema import (
    RecurrenceComponent,
    RoutineRecipeComponent,
    RoutineSummaryComponent,
)


class RoutineDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int

    name: str

    description: str | None

    start_date: date

    end_date: date | None

    recipes: list[RoutineRecipeComponent] = Field(
        default_factory=list
    )

    recurrence: RecurrenceComponent | None = None


class RoutineListResponse(BaseModel):
    items: list[RoutineSummaryComponent]

    page: int

    limit: int

    total: int


class RoutineSearchResponse(RoutineListResponse):
    query: str


class DeleteRoutineResponse(BaseModel):
    message: str