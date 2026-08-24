from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CartItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ingredient_id: int
    name: str | None = None
    quantity: Decimal
    unit: str


class CartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[CartItemResponse]