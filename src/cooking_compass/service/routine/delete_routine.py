from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cooking_compass.models.routines import Routine

# NOTE: adjust this import path to wherever
# invalidate_cart_cache actually lives
from cooking_compass.service.cart.get_cart import (
    invalidate_cart_cache,
)


async def delete_routine(
    db: AsyncSession,
    user_id: int,
    routine_id: int,
):

    routine = await db.scalar(
        select(Routine).where(
            Routine.id == routine_id,
            Routine.user_id == user_id,
        )
    )

    if routine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Routine not found",
        )

    try:

        await db.delete(routine)

        await db.commit()

        # -------------------------------------------------
        # Invalidate cached cart, since a deleted routine
        # removes its contribution to the cart.
        # -------------------------------------------------

        await invalidate_cart_cache(user_id)

    except Exception:

        await db.rollback()

        raise