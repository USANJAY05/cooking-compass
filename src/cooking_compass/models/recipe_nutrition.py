from typing import TYPE_CHECKING
from decimal import Decimal
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Numeric,
    ForeignKey,
    UniqueConstraint,
    Index,
    TIMESTAMP,
    text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


if TYPE_CHECKING:
    from .recipe import Recipe
    from .nutrients import Nutrient


class RecipeNutrition(Base):
    __tablename__ = "recipe_nutrition"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    recipe_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("recipe.id"),
        nullable=False,
    )

    nutrient_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("nutrients.id"),
        nullable=False,
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 6),
        nullable=False,
    )

    amount_per_serving: Mapped[Decimal] = mapped_column(
        Numeric(14, 6),
        nullable=False,
    )

    calculated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    recipe: Mapped["Recipe"] = relationship(
        "Recipe",
        back_populates="nutrition",
    )

    nutrient: Mapped["Nutrient"] = relationship(
        "Nutrient",
        back_populates="recipe_nutrition",
    )

    __table_args__ = (
        UniqueConstraint(
            "recipe_id",
            "nutrient_id",
            name="uk_recipe_nutrition",
        ),
        Index(
            "idx_recipe_nutrition_recipe",
            "recipe_id",
        ),
        Index(
            "idx_recipe_nutrition_nutrient",
            "nutrient_id",
        ),
    )