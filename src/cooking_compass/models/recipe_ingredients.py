from typing import TYPE_CHECKING
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    String,
    Integer,
    Numeric,
    ForeignKey,
    Index,
    text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


if TYPE_CHECKING:
    from .recipe import Recipe
    from .ingredients import Ingredient


class RecipeIngredient(TimestampMixin, Base):
    __tablename__ = "recipe_ingredients"

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

    ingredient_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("ingredients.id"),
        nullable=False,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
    )

    unit: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("1"),
    )

    recipe: Mapped["Recipe"] = relationship(
        "Recipe",
        back_populates="ingredients",
    )

    ingredient: Mapped["Ingredient"] = relationship(
        "Ingredient",
        back_populates="recipe_ingredients",
    )

    __table_args__ = (
        Index(
            "idx_recipe_ingredients_recipe",
            "recipe_id",
        ),
        Index(
            "idx_recipe_ingredients_ingredient",
            "ingredient_id",
        ),
    )