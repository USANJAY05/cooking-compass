from typing import TYPE_CHECKING
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    String,
    Text,
    Integer,
    Numeric,
    Enum,
    TIMESTAMP,
    ForeignKey,
    Index,
    text,
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from cooking_compass.schema.recipe.components_schema import CookedWeightUnit


if TYPE_CHECKING:
    from .users import User
    from .recipe_ingredients import RecipeIngredient
    from .recipe_nutrition import RecipeNutrition
    from .recipe_instructions import RecipeInstruction
    from .recipe_images import RecipeImage
    from .recipe_categories import RecipeCategory
    from .recipe_ratings import RecipeRating
    from .routine_items import RoutineItem
    from .recipe_tags import RecipeTag


class Recipe(TimestampMixin, Base):
    __tablename__ = "recipe"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    preparation_time: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    cooking_time: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    total_time: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    servings: Mapped[Decimal] = mapped_column(
        Numeric(8, 2),
        nullable=True,
    )

    visibility: Mapped[str] = mapped_column(
        Enum("PRIVATE", "PUBLIC"),
        nullable=False,
        server_default=text("'PRIVATE'"),
    )

    status: Mapped[str] = mapped_column(
        Enum("DRAFT", "PUBLISHED"),
        nullable=False,
        server_default=text("'DRAFT'"),
    )

    # ---------------------------------------------------------
    # Cooked weight (yield of the finished dish)
    # ---------------------------------------------------------
    #
    # cooked_weight_amount / cooked_weight_unit: exactly what the
    # user entered (e.g. "1.2" + "kg"), kept as-is for display.
    #
    # cooked_weight_grams: normalized value always in grams, computed
    # at write time. Use this for nutrition-per-gram / per-serving math
    # so you never have to re-parse units downstream.

    cooked_weight_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    cooked_weight_unit: Mapped[str | None] = mapped_column(
        Enum(*[u.value for u in CookedWeightUnit], name="cooked_weight_unit_enum"),
        nullable=True,
    )

    cooked_weight_grams: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="recipes",
    )

    ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        "RecipeIngredient",
        back_populates="recipe",
        cascade="all, delete-orphan",
    )

    nutrition: Mapped[list["RecipeNutrition"]] = relationship(
        "RecipeNutrition",
        back_populates="recipe",
        cascade="all, delete-orphan",
    )

    instructions: Mapped[list["RecipeInstruction"]] = relationship(
        "RecipeInstruction",
        back_populates="recipe",
        cascade="all, delete-orphan",
        foreign_keys="[RecipeInstruction.recipe_id]",
    )

    images: Mapped[list["RecipeImage"]] = relationship(
        "RecipeImage",
        back_populates="recipe",
        cascade="all, delete-orphan",
    )

    categories: Mapped[list["RecipeCategory"]] = relationship(
        "RecipeCategory",
        back_populates="recipe",
        cascade="all, delete-orphan",
    )

    tags: Mapped[list["RecipeTag"]] = relationship(
        "RecipeTag",
        back_populates="recipe",
        cascade="all, delete-orphan",
    )

    ratings: Mapped[list["RecipeRating"]] = relationship(
        "RecipeRating",
        back_populates="recipe",
        cascade="all, delete-orphan",
    )

    routine_items: Mapped[list["RoutineItem"]] = relationship(
        "RoutineItem",
        back_populates="recipe",
    )

    __table_args__ = (
        Index(
            "idx_recipes_user_id",
            "user_id",
        ),
        Index(
            "idx_recipes_visibility_status",
            "visibility",
            "status",
        ),
        Index(
            "idx_recipes_deleted_at",
            "deleted_at",
        ),
    )