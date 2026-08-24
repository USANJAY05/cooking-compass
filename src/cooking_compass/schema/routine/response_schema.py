from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .components_schema import (
    RecurrenceComponent,
    RoutineItemComponent,
    RoutineSummaryComponent,
)


class RoutineDetailResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    name: str

    description: str | None

    status: str

    recipes: list[RoutineItemComponent] = Field(
        default_factory=list
    )

    recurrence: RecurrenceComponent | None = None

    @model_validator(mode="before")
    @classmethod
    def build_response_dict(cls, obj):

        if isinstance(obj, dict):
            return obj

        items = getattr(obj, "items", []) or []

        recipes = []

        for item in items:
            recipe = getattr(item, "recipe", None)

            recipes.append({
                "recipe_id": item.recipe_id,
                "recipe_name": recipe.name if recipe else "",
                "recipe_thumbnail_url": None,
                "quantity": item.quantity,
                "quantity_unit": item.quantity_type,
            })

        return {
            "id": obj.id,
            "name": obj.name,
            "description": obj.description,
            "status": obj.status,
            "recipes": recipes,
            "recurrence": obj.recurrence,
        }


class RoutineListResponse(BaseModel):
    items: list[RoutineSummaryComponent]

    page: int

    limit: int

    total: int


class RoutineSearchResponse(
    RoutineListResponse
):
    query: str


class DeleteRoutineResponse(BaseModel):
    message: str
