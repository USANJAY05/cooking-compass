from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    String,
    Text,
    Enum,
    ForeignKey,
    Index,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


if TYPE_CHECKING:
    from .users import User
    from .routine_items import RoutineItem
    from .routine_recurrence import RoutineRecurrence


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
        Enum(
            "ACTIVE",
            "INACTIVE",
            "COMPLETED",
        ),
        nullable=False,
        server_default=text("'ACTIVE'"),
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

    recurrence: Mapped["RoutineRecurrence | None"] = relationship(
        "RoutineRecurrence",
        back_populates="routine",
        uselist=False,
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
    )