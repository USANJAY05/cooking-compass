from pydantic import BaseModel, ConfigDict, Field


class CartItemComponent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ingredient_id: int = Field(gt=0)

    name: str = Field(
        min_length=1,
        max_length=150,
    )

    quantity: float = Field(
        gt=0,
    )

    unit: str = Field(
        min_length=1,
        max_length=50,
    )

    checked: bool = False