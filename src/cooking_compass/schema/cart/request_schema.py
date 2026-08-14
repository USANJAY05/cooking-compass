from datetime import date

from pydantic import BaseModel, Field


# ---------------------------------------------------------
# GET /cart
# ---------------------------------------------------------

class GetCartRequest(BaseModel):
    from_date: date | None = None
    to_date: date | None = None


# ---------------------------------------------------------
# POST /cart/generate
# ---------------------------------------------------------

class GenerateCartRequest(BaseModel):
    from_date: date
    to_date: date

    def validate_dates(self):
        if self.to_date < self.from_date:
            raise ValueError(
                "to_date cannot be before from_date"
            )


# ---------------------------------------------------------
# PUT /cart/items/{ingredient_id}
# ---------------------------------------------------------

class UpdateCartItemRequest(BaseModel):
    quantity: float | None = Field(
        default=None,
        gt=0,
    )

    checked: bool | None = None