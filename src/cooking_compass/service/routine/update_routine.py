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
    UpdateRoutineRequest,
)

# NOTE: adjust this import path to wherever
# invalidate_cart_cache actually lives
from cooking_compass.service.cart.get_cart import (
    invalidate_cart_cache,
)


async def update_routine(
    db: AsyncSession,
    user_id: int,
    routine_id: int,
    request: UpdateRoutineRequest,
):

    routine = await db.scalar(
        select(Routine)
        .where(
            Routine.id == routine_id,
            Routine.user_id == user_id,
        )
        .options(
            selectinload(Routine.items),
            selectinload(Routine.recurrence),
        )
    )

    if routine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Routine not found",
        )

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

        # -------------------------------------------------
        # Update routine
        # -------------------------------------------------

        routine.name = request.name
        routine.description = request.description

        # -------------------------------------------------
        # Replace routine items
        # -------------------------------------------------

        routine.items.clear()

        for item in request.items:

            routine_item = RoutineItem(
                recipe_id=item.recipe_id,
                quantity=item.quantity,
                quantity_type=item.quantity_unit,
            )

            routine.items.append(
                routine_item
            )

        # -------------------------------------------------
        # Update recurrence
        # -------------------------------------------------

        recurrence_data = request.recurrence

        days_of_week = None

        if recurrence_data.days_of_week:
            days_of_week = ",".join(
                str(day)
                for day in recurrence_data.days_of_week
            )

        if routine.recurrence is None:

            routine.recurrence = RoutineRecurrence(
                frequency=recurrence_data.frequency,
                interval_value=recurrence_data.interval,
                days_of_week=days_of_week,
                start_date=recurrence_data.start_date,
                end_date=recurrence_data.end_date,
                occurrence_count=(
                    recurrence_data.occurrence_count
                ),
            )

        else:

            routine.recurrence.frequency = (
                recurrence_data.frequency
            )

            routine.recurrence.interval_value = (
                recurrence_data.interval
            )

            routine.recurrence.days_of_week = (
                days_of_week
            )

            routine.recurrence.start_date = (
                recurrence_data.start_date
            )

            routine.recurrence.end_date = (
                recurrence_data.end_date
            )

            routine.recurrence.occurrence_count = (
                recurrence_data.occurrence_count
            )

        await db.commit()

        # -------------------------------------------------
        # Invalidate cached cart, since routine items /
        # quantities may have changed.
        # -------------------------------------------------

        await invalidate_cart_cache(user_id)

    except Exception:

        await db.rollback()

        raise

    return await db.scalar(
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