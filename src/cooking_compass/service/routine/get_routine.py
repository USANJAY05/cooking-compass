from fastapi import HTTPException, status

from sqlalchemy import (
    select,
    func,
    asc,
    desc,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cooking_compass.models.routines import Routine
from cooking_compass.models.routine_items import RoutineItem
from cooking_compass.models.recipe import Recipe


async def get_routine(
    db: AsyncSession,
    user_id: int,
    routine_id: int,
):

    routine = await db.scalar(
        select(Routine)
        .where(
            Routine.id == routine_id,
            Routine.user_id == user_id,
        )
        .options(
            selectinload(Routine.items)
            .selectinload(RoutineItem.recipe),
            selectinload(Routine.recurrence),
        )
    )

    if routine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Routine not found",
        )

    return routine


async def get_routines(
    db: AsyncSession,
    user_id: int,
    scope: str = "mine",
    page: int = 1,
    limit: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
):

    query = select(Routine)

    if scope == "mine":
        query = query.where(
            Routine.user_id == user_id
        )

    sort_column = getattr(
        Routine,
        sort_by,
        Routine.created_at,
    )

    if sort_order == "asc":
        query = query.order_by(
            asc(sort_column)
        )
    else:
        query = query.order_by(
            desc(sort_column)
        )

    total = await db.scalar(
        select(func.count())
        .select_from(
            query.subquery()
        )
    )

    result = await db.scalars(
        query
        .offset((page - 1) * limit)
        .limit(limit)
    )
    items = result.all()

    return items, total or 0


async def search_routines(
    db: AsyncSession,
    user_id: int,
    q: str,
    scope: str = "mine",
    page: int = 1,
    limit: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
):

    query = select(Routine).where(
        Routine.name.ilike(f"%{q}%")
    )

    if scope == "mine":
        query = query.where(
            Routine.user_id == user_id
        )

    sort_column = getattr(
        Routine,
        sort_by,
        Routine.created_at,
    )

    if sort_order == "asc":
        query = query.order_by(
            asc(sort_column)
        )
    else:
        query = query.order_by(
            desc(sort_column)
        )

    total = await db.scalar(
        select(func.count())
        .select_from(
            query.subquery()
        )
    )

    result = await db.scalars(
        query
        .offset((page - 1) * limit)
        .limit(limit)
    )
    items = result.all()

    return items, total or 0