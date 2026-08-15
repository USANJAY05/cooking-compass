from typing import TYPE_CHECKING
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    ForeignKey,
    TIMESTAMP,
    PrimaryKeyConstraint,
    Index,
    text
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


if TYPE_CHECKING:
    from .recipe import Recipe
    from .categories import Category


class RecipeCategory(Base):
    __tablename__ = "recipe_categories"

    recipe_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("recipe.id"),
        nullable=False,
    )

    category_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("categories.id"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    recipe: Mapped["Recipe"] = relationship(
        "Recipe",
        back_populates="categories",
    )

    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="recipes",
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "recipe_id",
            "category_id",
        ),
        Index(
            "idx_recipe_categories_category",
            "category_id",
        ),
    )