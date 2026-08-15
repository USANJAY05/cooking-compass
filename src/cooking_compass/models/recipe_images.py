from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Integer,
    Enum,
    ForeignKey,
    UniqueConstraint,
    Index,
    text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


if TYPE_CHECKING:
    from .recipe import Recipe
    from .images import Image


class RecipeImage(Base):
    __tablename__ = "recipe_images"

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

    image_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("images.id"),
        nullable=False,
    )

    image_type: Mapped[str] = mapped_column(
        Enum("THUMBNAIL", "GALLERY"),
        nullable=False,
        server_default=text("'GALLERY'"),
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("1"),
    )

    recipe: Mapped["Recipe"] = relationship(
        "Recipe",
        back_populates="images",
    )

    image: Mapped["Image"] = relationship(
        "Image",
        back_populates="recipe_images",
    )

    __table_args__ = (
        UniqueConstraint(
            "recipe_id",
            "image_id",
            name="uk_recipe_image",
        ),
        Index(
            "idx_recipe_images_recipe",
            "recipe_id",
        ),
    )