from typing import TYPE_CHECKING
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    String,
    Numeric,
    ForeignKey,
    UniqueConstraint,
    Index,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


if TYPE_CHECKING:
    from .ingredients import Ingredient
    from .nutrients import Nutrient


class IngredientNutrient(TimestampMixin, Base):
    __tablename__ = "ingredient_nutrients"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    ingredient_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("ingredients.id"),
        nullable=False,
    )

    nutrient_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("nutrients.id"),
        nullable=False,
    )

    amount_per_100g: Mapped[Decimal] = mapped_column(
        Numeric(14, 6),
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="USDA",
    )

    source_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    ingredient: Mapped["Ingredient"] = relationship(
        "Ingredient",
        back_populates="nutrients",
    )

    nutrient: Mapped["Nutrient"] = relationship(
        "Nutrient",
        back_populates="ingredient_nutrients",
    )

    __table_args__ = (
        UniqueConstraint(
            "ingredient_id",
            "nutrient_id",
            name="uk_ingredient_nutrient",
        ),
        Index(
            "idx_ingredient_nutrients_ingredient",
            "ingredient_id",
        ),
        Index(
            "idx_ingredient_nutrients_nutrient",
            "nutrient_id",
        ),
    )