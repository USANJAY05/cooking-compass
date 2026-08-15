from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


if TYPE_CHECKING:
    from .recipe_images import RecipeImage
    from .instruction_images import InstructionImage


class Image(TimestampMixin, Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    storage_key: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        unique=True,
    )

    file_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    width: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    height: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    recipe_images: Mapped[list["RecipeImage"]] = relationship(
        "RecipeImage",
        back_populates="image",
    )

    instruction_images: Mapped[list["InstructionImage"]] = relationship(
        "InstructionImage",
        back_populates="image",
    )