from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Integer,
    Text,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


if TYPE_CHECKING:
    from .recipe import Recipe
    from .instruction_images import InstructionImage


class RecipeInstruction(TimestampMixin, Base):
    __tablename__ = "recipe_instructions"

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

    step_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    instruction_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    timer_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    tip: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reference_recipe_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("recipe.id"),
        nullable=True,
    )

    recipe: Mapped["Recipe"] = relationship(
        "Recipe",
        back_populates="instructions",
        foreign_keys=[recipe_id],
    )

    reference_recipe: Mapped["Recipe"] = relationship(
        "Recipe",
        foreign_keys=[reference_recipe_id],
    )

    images: Mapped[list["InstructionImage"]] = relationship(
        "InstructionImage",
        back_populates="instruction",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "recipe_id",
            "step_number",
            name="uk_recipe_step",
        ),
        Index(
            "idx_instructions_recipe",
            "recipe_id",
        ),
        Index(
            "idx_instructions_reference_recipe",
            "reference_recipe_id",
        ),
    )