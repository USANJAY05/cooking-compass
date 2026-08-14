from datetime import datetime

from sqlalchemy import (
    DECIMAL,
    Enum,
    ForeignKey,
    Index,
    String,
    TIMESTAMP,
    text,
)
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, TEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.cooking_compass.core.db import Base


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        TEXT,
        nullable=True,
    )

    preparation_time: Mapped[int | None] = mapped_column(
        INTEGER(unsigned=True),
        nullable=True,
    )

    cooking_time: Mapped[int | None] = mapped_column(
        INTEGER(unsigned=True),
        nullable=True,
    )

    total_time: Mapped[int | None] = mapped_column(
        INTEGER(unsigned=True),
        nullable=True,
    )

    servings: Mapped[float] = mapped_column(
        DECIMAL(8, 2),
        nullable=False,
    )

    visibility: Mapped[str] = mapped_column(
        Enum("PRIVATE", "PUBLIC"),
        nullable=False,
        server_default=text("'PRIVATE'"),
    )

    status: Mapped[str] = mapped_column(
        Enum("DRAFT", "PUBLISHED"),
        nullable=False,
        server_default=text("'DRAFT'"),
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="recipes",
    )

    __table_args__ = (
        Index(
            "idx_recipes_user_id",
            "user_id",
        ),
        Index(
            "idx_recipes_visibility_status",
            "visibility",
            "status",
        ),
        Index(
            "idx_recipes_deleted_at",
            "deleted_at",
        ),
    )