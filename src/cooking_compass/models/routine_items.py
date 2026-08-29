from typing import TYPE_CHECKING
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Numeric,
    Enum,
    ForeignKey,
    Index,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


if TYPE_CHECKING:
    from .routines import Routine
    from .recipe import Recipe


class RoutineItem(TimestampMixin, Base):
    __tablename__ = "routine_items"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    routine_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("routines.id"),
        nullable=False,
    )

    recipe_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("recipe.id"),
        nullable=False,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    quantity_type: Mapped[str] = mapped_column(
        Enum(
            "SERVING",
            "G",
            "KG",
            "ML",
            "L",
        ),
        nullable=False,
    )

    routine: Mapped["Routine"] = relationship(
        "Routine",
        back_populates="items",
    )

    recipe: Mapped["Recipe"] = relationship(
        "Recipe",
        back_populates="routine_items",
    )

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="chk_routine_item_quantity",
        ),
        Index(
            "idx_routine_items_routine",
            "routine_id",
        ),
        Index(
            "idx_routine_items_recipe",
            "recipe_id",
        ),
    )