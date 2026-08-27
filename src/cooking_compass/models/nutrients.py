from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


if TYPE_CHECKING:
    from .ingredient_nutrients import IngredientNutrient
    from .recipe_nutrition import RecipeNutrition


class NutrientType(str, Enum):
    MACRO = "macro"
    MICRO = "micro"
    OTHER = "other"


class Nutrient(TimestampMixin, Base):
    __tablename__ = "nutrients"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
    )

    unit: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    nutrition_type: Mapped[NutrientType] = mapped_column(
        String(20),
        nullable=False,
        default=NutrientType.OTHER,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ingredient_nutrients: Mapped[list["IngredientNutrient"]] = relationship(
        "IngredientNutrient",
        back_populates="nutrient",
    )

    recipe_nutrition: Mapped[list["RecipeNutrition"]] = relationship(
        "RecipeNutrition",
        back_populates="nutrient",
    )

    __table_args__ = (
        Index(
            "idx_nutrients_name",
            "name",
        ),
    )