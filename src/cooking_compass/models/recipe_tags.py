from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .recipe import Recipe
    from .tags import Tag


class RecipeTag(Base):
    __tablename__ = "recipe_tags"

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

    tag_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tags.id"),
        nullable=False,
    )

    recipe: Mapped["Recipe"] = relationship(
        "Recipe",
        back_populates="tags",
    )

    tag: Mapped["Tag"] = relationship(
        "Tag",
        back_populates="recipe_tags",
    )

    __table_args__ = (
        UniqueConstraint("recipe_id", "tag_id", name="uk_recipe_tag"),
        Index("idx_recipe_tags_recipe", "recipe_id"),
    )