# cooking_compass/schema/ingredient/request_schema.py
from pydantic import BaseModel, Field


class CreateIngredientRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    source: str = Field(default="USDA", max_length=50)
    external_reference: str | None = Field(default=None, max_length=255)
    default_unit: str = Field(min_length=1, max_length=30)


class UpdateIngredientRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    source: str | None = Field(default=None, max_length=50)
    external_reference: str | None = Field(default=None, max_length=255)
    default_unit: str | None = Field(default=None, min_length=1, max_length=30)