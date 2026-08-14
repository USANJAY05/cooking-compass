from datetime import date

from pydantic import BaseModel, Field

from .components_schema import CartItemComponent


class CartResponse(BaseModel):
    from_date: date | None

    to_date: date | None

    items: list[CartItemComponent] = Field(
        default_factory=list
    )

    total_items: int

    checked_items: int


class GenerateCartResponse(BaseModel):
    from_date: date

    to_date: date

    items: list[CartItemComponent] = Field(
        default_factory=list
    )

    total_items: int


class UpdateCartItemResponse(BaseModel):
    item: CartItemComponent