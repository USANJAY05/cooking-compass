from typing import TYPE_CHECKING
from datetime import date

from sqlalchemy import (
    BigInteger,
    String,
    Integer,
    Date,
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


class RoutineRecurrence(TimestampMixin, Base):
    __tablename__ = "routine_recurrence"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    routine_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("routines.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    frequency: Mapped[str] = mapped_column(
        Enum(
            "DAILY",
            "WEEKLY",
            "MONTHLY",
        ),
        nullable=False,
    )

    interval_value: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("1"),
    )

    days_of_week: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    occurrence_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    routine: Mapped["Routine"] = relationship(
        "Routine",
        back_populates="recurrence",
    )

    __table_args__ = (
        CheckConstraint(
            "interval_value > 0",
            name="chk_routine_recurrence_interval",
        ),
        CheckConstraint(
            "occurrence_count IS NULL OR occurrence_count > 0",
            name="chk_routine_recurrence_occurrence",
        ),
        Index(
            "idx_routine_recurrence_routine",
            "routine_id",
        ),
        Index(
            "idx_routine_recurrence_dates",
            "start_date",
            "end_date",
        ),
    )