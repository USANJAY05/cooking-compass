from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


if TYPE_CHECKING:
    from .recipe_ingredients import RecipeIngredient
    from .ingredient_nutrients import IngredientNutrient


class Ingredient(TimestampMixin, Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="USDA",
    )

    external_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    default_unit: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    recipe_ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        "RecipeIngredient",
        back_populates="ingredient",
    )

    nutrients: Mapped[list["IngredientNutrient"]] = relationship(
        "IngredientNutrient",
        back_populates="ingredient",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index(
            "idx_ingredients_name",
            "name",
        ),
        Index(
            "idx_ingredients_external_reference",
            "external_reference",
        ),
    )