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
    text
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


if TYPE_CHECKING:
    from .users import User
    from .recipe_ingredients import RecipeIngredient
    from .recipe_nutrition import RecipeNutrition
    from .recipe_instructions import RecipeInstruction
    from .recipe_images import RecipeImage
    from .recipe_categories import RecipeCategory
    from .recipe_ratings import RecipeRating
    from .routine_items import RoutineItem


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
        nullable=False,
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

    deleted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        nullable=True
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