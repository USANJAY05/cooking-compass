from typing import TYPE_CHECKING
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Numeric,
    Date,
    SmallInteger,
    Enum,
    ForeignKey,
    Index,
    CheckConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


if TYPE_CHECKING:
    from .routines import Routine
    from .recipe import Recipe
    from .routine_recurrence import RoutineRecurrence


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

    meal_type: Mapped[str] = mapped_column(
        Enum(
            "BREAKFAST",
            "LUNCH",
            "DINNER",
            "SNACK",
        ),
        nullable=False,
    )

    scheduled_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    day_of_week: Mapped[int | None] = mapped_column(
        SmallInteger,
        nullable=True,
    )

    servings: Mapped[Decimal] = mapped_column(
        Numeric(8, 2),
        nullable=False,
        server_default=text("1"),
    )

    routine: Mapped["Routine"] = relationship(
        "Routine",
        back_populates="items",
    )

    recipe: Mapped["Recipe"] = relationship(
        "Recipe",
        back_populates="routine_items",
    )

    recurrence: Mapped["RoutineRecurrence | None"] = relationship(
        "RoutineRecurrence",
        back_populates="routine_item",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "day_of_week IS NULL OR day_of_week BETWEEN 1 AND 7",
            name="chk_routine_day_of_week",
        ),
        Index(
            "idx_routine_items_routine",
            "routine_id",
        ),
        Index(
            "idx_routine_items_recipe",
            "recipe_id",
        ),
        Index(
            "idx_routine_items_date",
            "scheduled_date",
        ),
        Index(
            "idx_routine_items_day",
            "day_of_week",
        ),
    )