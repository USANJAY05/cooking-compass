from typing import TYPE_CHECKING
from datetime import date

from sqlalchemy import (
    BigInteger,
    String,
    Text,
    Enum,
    Date,
    ForeignKey,
    Index,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


if TYPE_CHECKING:
    from .users import User
    from .routine_items import RoutineItem


class Routine(TimestampMixin, Base):
    __tablename__ = "routines"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        Enum("ACTIVE", "INACTIVE", "COMPLETED"),
        nullable=False,
        server_default=text("'ACTIVE'"),
    )

    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="routines",
    )

    items: Mapped[list["RoutineItem"]] = relationship(
        "RoutineItem",
        back_populates="routine",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index(
            "idx_routines_user",
            "user_id",
        ),
        Index(
            "idx_routines_status",
            "status",
        ),
        Index(
            "idx_routines_dates",
            "start_date",
            "end_date",
        ),
    )