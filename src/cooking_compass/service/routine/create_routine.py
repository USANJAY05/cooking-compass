from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cooking_compass.models.routines import Routine
from cooking_compass.models.routine_items import RoutineItem
from cooking_compass.models.routine_recurrence import (
    RoutineRecurrence,
)
from cooking_compass.models.recipe import Recipe

from cooking_compass.schema.routine.request_schema import (
    CreateRoutineRequest,
)

# NOTE: adjust this import path to wherever
# invalidate_cart_cache actually lives
from cooking_compass.service.cart.get_cart import (
    invalidate_cart_cache,
)


async def create_routine(
    db: AsyncSession,
    user_id: int,
    request: CreateRoutineRequest,
):

    recipe_ids = [
        item.recipe_id
        for item in request.items
    ]

    result = await db.scalars(
        select(Recipe).where(
            Recipe.id.in_(recipe_ids),
            Recipe.user_id == user_id,
            Recipe.deleted_at.is_(None),
        )
    )
    recipes = result.all()

    recipe_map = {
        recipe.id: recipe
        for recipe in recipes
    }

    missing_recipe_ids = [
        recipe_id
        for recipe_id in recipe_ids
        if recipe_id not in recipe_map
    ]

    if missing_recipe_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Recipe(s) not found: "
                f"{missing_recipe_ids}"
            ),
        )

    try:

        routine = Routine(
            user_id=user_id,
            name=request.name,
            description=request.description,
        )

        db.add(routine)

        await db.flush()

        for item in request.items:

            routine_item = RoutineItem(
                routine_id=routine.id,
                recipe_id=item.recipe_id,
                quantity=item.quantity,
                quantity_type=item.quantity_unit,
            )

            db.add(routine_item)

        recurrence = request.recurrence

        days_of_week = None

        if recurrence.days_of_week:
            days_of_week = ",".join(
                str(day)
                for day in recurrence.days_of_week
            )

        routine_recurrence = RoutineRecurrence(
            routine_id=routine.id,
            frequency=recurrence.frequency,
            interval_value=recurrence.interval,
            days_of_week=days_of_week,
            start_date=recurrence.start_date,
            end_date=recurrence.end_date,
            occurrence_count=recurrence.occurrence_count,
        )

        db.add(routine_recurrence)

        await db.commit()

        # -------------------------------------------------
        # Invalidate cached cart, since a new routine
        # changes what should be in it.
        # -------------------------------------------------

        await invalidate_cart_cache(user_id)

    except Exception:

        await db.rollback()

        raise

    return await db.scalar(
        select(Routine)
        .where(Routine.id == routine.id)
        .options(
            selectinload(Routine.items)
            .selectinload(RoutineItem.recipe),
            selectinload(Routine.recurrence),
        )
    )