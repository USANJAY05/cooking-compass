from typing import TYPE_CHECKING

from sqlalchemy import String, BigInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


if TYPE_CHECKING:
    from .recipe import Recipe
    from .recipe_ratings import RecipeRating
    from .routines import Routine


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    keycloak_user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True
    )

    recipes: Mapped[list["Recipe"]] = relationship(
        "Recipe",
        back_populates="user",
    )

    ratings: Mapped[list["RecipeRating"]] = relationship(
        "RecipeRating",
        back_populates="user",
    )

    routines: Mapped[list["Routine"]] = relationship(
        "Routine",
        back_populates="user",
    )