from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Integer,
    ForeignKey,
    UniqueConstraint,
    Index,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


if TYPE_CHECKING:
    from .recipe_instructions import RecipeInstruction
    from .images import Image


class InstructionImage(Base):
    __tablename__ = "instruction_images"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    instruction_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("recipe_instructions.id"),
        nullable=False,
    )

    image_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("images.id"),
        nullable=False,
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("1"),
    )

    instruction: Mapped["RecipeInstruction"] = relationship(
        "RecipeInstruction",
        back_populates="images",
    )

    image: Mapped["Image"] = relationship(
        "Image",
        back_populates="instruction_images",
    )

    __table_args__ = (
        UniqueConstraint(
            "instruction_id",
            "image_id",
            name="uk_instruction_image",
        ),
        Index(
            "idx_instruction_images_instruction",
            "instruction_id",
        ),
    )