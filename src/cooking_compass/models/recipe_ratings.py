from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Text,
    SmallInteger,
    ForeignKey,
    UniqueConstraint,
    Index,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


if TYPE_CHECKING:
    from .recipe import Recipe
    from .users import User


class RecipeRating(TimestampMixin, Base):
    __tablename__ = "recipe_ratings"

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

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    rating: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )

    review: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    recipe: Mapped["Recipe"] = relationship(
        "Recipe",
        back_populates="ratings",
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="ratings",
    )

    __table_args__ = (
        CheckConstraint(
            "rating BETWEEN 1 AND 5",
            name="chk_recipe_rating",
        ),
        UniqueConstraint(
            "recipe_id",
            "user_id",
            name="uk_recipe_rating_user",
        ),
        Index(
            "idx_recipe_ratings_recipe",
            "recipe_id",
        ),
        Index(
            "idx_recipe_ratings_user",
            "user_id",
        ),
    )