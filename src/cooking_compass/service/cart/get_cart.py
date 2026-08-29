from collections import defaultdict
from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cooking_compass.core.redis import get_redis

from cooking_compass.models.routines import Routine
from cooking_compass.models.routine_items import RoutineItem
from cooking_compass.models.recipe import Recipe
from cooking_compass.models.recipe_ingredients import RecipeIngredient

from cooking_compass.schema.cart.response_schema import (
    CartItemResponse,
    CartResponse,
)


CART_TTL = 60 * 60 * 24 * 7


# =========================================================
# RECURRENCE HELPERS
# =========================================================

def parse_days_of_week(
    value: str | list[int] | None,
) -> list[int]:
    """
    Convert the database representation of days_of_week
    into a list of weekday numbers.

    Database example:

        "0,2,4"

    Means:

        Monday    = 0
        Wednesday = 2
        Friday    = 4
    """

    if value is None:
        return []

    if isinstance(value, list):
        values = value

    elif isinstance(value, str):
        if not value.strip():
            return []

        values = value.split(",")

    else:
        return []

    result = []

    for item in values:
        try:
            day = int(item)

            if 0 <= day <= 6:
                result.append(day)

        except (TypeError, ValueError):
            continue

    return sorted(set(result))


def get_recurrence_occurrences(
    recurrence,
    window_start: date,
    window_end: date,
) -> list[date]:
    """
    Calculate every occurrence of a routine inside the
    requested cart window.

    Supports:

        DAILY
        WEEKLY
        MONTHLY

    Respects:

        interval_value
        days_of_week
        start_date
        end_date
        occurrence_count
    """

    if recurrence is None:
        return []

    recurrence_start = recurrence.start_date

    # -----------------------------------------------------
    # Effective window
    # -----------------------------------------------------

    start_date = max(
        recurrence_start,
        window_start,
    )

    recurrence_end = recurrence.end_date

    if recurrence_end is not None:
        end_date = min(
            recurrence_end,
            window_end,
        )
    else:
        end_date = window_end

    if start_date > end_date:
        return []

    frequency = (
        recurrence.frequency or ""
    ).upper()

    interval = max(
        int(
            recurrence.interval_value or 1
        ),
        1,
    )

    occurrence_count = (
        recurrence.occurrence_count
    )

    # =====================================================
    # DAILY
    # =====================================================

    if frequency == "DAILY":

        occurrences = []

        current_date = recurrence_start

        occurrence_number = 0

        while current_date <= end_date:

            occurrence_number += 1

            # occurrence_count applies to the entire
            # recurrence starting from start_date.
            if (
                occurrence_count is not None
                and occurrence_number
                > occurrence_count
            ):
                break

            if current_date >= start_date:
                occurrences.append(
                    current_date
                )

            current_date += timedelta(
                days=interval
            )

        return occurrences

    # =====================================================
    # WEEKLY
    # =====================================================

    if frequency == "WEEKLY":

        occurrences = []

        days_of_week = parse_days_of_week(
            recurrence.days_of_week
        )

        # -------------------------------------------------
        # If days_of_week isn't specified, use the weekday
        # of the recurrence start date.
        # -------------------------------------------------

        if not days_of_week:
            days_of_week = [
                recurrence_start.weekday()
            ]

        recurrence_week_start = (
            recurrence_start
            - timedelta(
                days=recurrence_start.weekday()
            )
        )

        current_week_start = (
            recurrence_week_start
        )

        occurrence_number = 0

        while current_week_start <= end_date:

            weeks_since_start = (
                current_week_start
                - recurrence_week_start
            ).days // 7

            # Every interval_value weeks.
            if (
                weeks_since_start % interval
                == 0
            ):

                for weekday in days_of_week:

                    occurrence_date = (
                        current_week_start
                        + timedelta(
                            days=weekday
                        )
                    )

                    # Don't create an occurrence before
                    # the recurrence actually starts.
                    if (
                        occurrence_date
                        < recurrence_start
                    ):
                        continue

                    if occurrence_date > end_date:
                        continue

                    occurrence_number += 1

                    if (
                        occurrence_count is not None
                        and occurrence_number
                        > occurrence_count
                    ):
                        return occurrences

                    if occurrence_date >= start_date:
                        occurrences.append(
                            occurrence_date
                        )

            current_week_start += timedelta(
                weeks=1
            )

        return sorted(occurrences)

    # =====================================================
    # MONTHLY
    # =====================================================

    if frequency == "MONTHLY":

        occurrences = []

        occurrence_number = 0

        month_index = (
            recurrence_start.year * 12
            + recurrence_start.month
            - 1
        )

        start_month_index = month_index

        while True:

            year = (
                month_index // 12
            )

            month = (
                month_index % 12
            ) + 1

            last_day = monthrange(
                year,
                month,
            )[1]

            # If recurrence starts on the 31st, February
            # becomes February's last day.
            occurrence_day = min(
                recurrence_start.day,
                last_day,
            )

            occurrence_date = date(
                year,
                month,
                occurrence_day,
            )

            if occurrence_date > end_date:
                break

            months_since_start = (
                month_index
                - start_month_index
            )

            if (
                months_since_start % interval
                == 0
            ):

                occurrence_number += 1

                if (
                    occurrence_count is not None
                    and occurrence_number
                    > occurrence_count
                ):
                    break

                if occurrence_date >= start_date:
                    occurrences.append(
                        occurrence_date
                    )

            month_index += 1

        return occurrences

    return []


# =========================================================
# RECIPE MULTIPLIER
# =========================================================

def calculate_recipe_multiplier(
    routine_item: RoutineItem,
    recipe: Recipe,
) -> Decimal | None:
    """
    Calculate the ingredient multiplier for ONE occurrence
    of the routine item.

    Example:

        Recipe servings = 4
        Routine quantity = 2 SERVING

        multiplier = 2 / 4
                    = 0.5
    """

    quantity = Decimal(
        str(routine_item.quantity)
    )

    quantity_type = (
        routine_item.quantity_type or ""
    ).upper()

    # =====================================================
    # SERVING
    # =====================================================

    if quantity_type == "SERVING":

        servings = Decimal(
            str(recipe.servings or 0)
        )

        if servings <= 0:
            return None

        return (
            quantity
            / servings
        )

    # =====================================================
    # G / KG / ML / L
    # =====================================================

    total_recipe_quantity = Decimal("0")

    for recipe_ingredient in recipe.ingredients:

        ingredient_unit = (
            recipe_ingredient.unit or ""
        ).upper()

        if ingredient_unit == quantity_type:

            total_recipe_quantity += Decimal(
                str(
                    recipe_ingredient.quantity
                )
            )

    if total_recipe_quantity <= 0:
        return None

    return (
        quantity
        / total_recipe_quantity
    )


# =========================================================
# GET CART SERVICE
# =========================================================

async def get_cart_service(
    days: int,
    current_user: dict,
    db: AsyncSession,
) -> CartResponse:

    user_id = current_user["id"]

    # -----------------------------------------------------
    # Normalize days
    # -----------------------------------------------------

    days = max(days, 1)

    redis_client = get_redis()

    cache_key = (
        f"cart:v2:{user_id}:{days}"
    )

    # =====================================================
    # 1. CHECK REDIS
    # =====================================================

    cached_cart = await redis_client.get(
        cache_key
    )

    if cached_cart:
        return CartResponse.model_validate_json(
            cached_cart
        )

    # =====================================================
    # 2. CART WINDOW
    # =====================================================

    window_start = date.today()

    window_end = (
        window_start
        + timedelta(
            days=days - 1
        )
    )

    # =====================================================
    # 3. GET ACTIVE ROUTINES
    # =====================================================

    result = await db.execute(
        select(Routine)
        .where(
            Routine.user_id == user_id,
            Routine.status == "ACTIVE",
        )
        .options(
            selectinload(
                Routine.items
            )
            .selectinload(
                RoutineItem.recipe
            )
            .selectinload(
                Recipe.ingredients
            )
            .selectinload(
                RecipeIngredient.ingredient
            ),

            selectinload(
                Routine.recurrence
            ),
        )
    )

    routines = (
        result
        .scalars()
        .unique()
        .all()
    )

    # =====================================================
    # 4. AGGREGATION
    # =====================================================

    ingredient_quantities: dict[
        int,
        Decimal,
    ] = defaultdict(
        lambda: Decimal("0")
    )

    ingredient_units: dict[
        int,
        str,
    ] = {}

    ingredient_names: dict[
        int,
        str,
    ] = {}

    # =====================================================
    # 5. PROCESS ROUTINES
    # =====================================================

    for routine in routines:

        recurrence = getattr(
            routine,
            "recurrence",
            None,
        )

        if recurrence is None:
            continue

        # -------------------------------------------------
        # Get actual recurrence dates.
        # -------------------------------------------------

        occurrences = (
            get_recurrence_occurrences(
                recurrence=recurrence,
                window_start=window_start,
                window_end=window_end,
            )
        )

        if not occurrences:
            continue

        # -------------------------------------------------
        # Number of times this routine runs in the
        # requested cart window.
        # -------------------------------------------------

        occurrence_count = Decimal(
            len(occurrences)
        )

        # -------------------------------------------------
        # Every recipe in this routine occurs each time
        # the routine occurs.
        # -------------------------------------------------

        for routine_item in routine.items:

            recipe = routine_item.recipe

            if recipe is None:
                continue

            # -------------------------------------------------
            # Quantity for ONE occurrence.
            # -------------------------------------------------

            multiplier = (
                calculate_recipe_multiplier(
                    routine_item=routine_item,
                    recipe=recipe,
                )
            )

            if multiplier is None:
                continue

            # -------------------------------------------------
            # Quantity for ALL occurrences.
            #
            # Example:
            #
            # 1 serving Biryani
            # DAILY
            # 5 occurrences
            #
            # total_multiplier =
            #
            #     1/recipe_servings × 5
            # -------------------------------------------------

            total_multiplier = (
                multiplier
                * occurrence_count
            )

            # -------------------------------------------------
            # Add recipe ingredients.
            # -------------------------------------------------

            for recipe_ingredient in (
                recipe.ingredients
            ):

                ingredient_id = (
                    recipe_ingredient.ingredient_id
                )

                ingredient_quantity = Decimal(
                    str(
                        recipe_ingredient.quantity
                    )
                )

                calculated_quantity = (
                    ingredient_quantity
                    * total_multiplier
                )

                ingredient_quantities[
                    ingredient_id
                ] += calculated_quantity

                # -------------------------------------------------
                # Unit
                # -------------------------------------------------

                ingredient_units[
                    ingredient_id
                ] = recipe_ingredient.unit

                # -------------------------------------------------
                # Ingredient name
                # -------------------------------------------------

                ingredient = (
                    recipe_ingredient.ingredient
                )

                if ingredient is not None:

                    ingredient_names[
                        ingredient_id
                    ] = ingredient.name

    # =====================================================
    # 6. BUILD RESPONSE
    # =====================================================

    cart_items = []

    for (
        ingredient_id,
        quantity,
    ) in ingredient_quantities.items():

        if quantity <= 0:
            continue

        cart_items.append(
            CartItemResponse(
                ingredient_id=ingredient_id,
                name=ingredient_names.get(
                    ingredient_id
                ),
                quantity=quantity,
                unit=ingredient_units[
                    ingredient_id
                ],
            )
        )

    # Stable response ordering.
    cart_items.sort(
        key=lambda item: (
            item.name or ""
        ).lower()
    )

    response = CartResponse(
        items=cart_items,
    )

    # =====================================================
    # 7. CACHE
    # =====================================================

    await redis_client.set(
        cache_key,
        response.model_dump_json(),
        ex=CART_TTL,
    )

    return response


# =========================================================
# INVALIDATE CART CACHE
# =========================================================

async def invalidate_cart_cache(
    user_id: int,
) -> None:
    """
    Delete every cart cache variant for this user.

    Example:

        cart:v2:10:1
        cart:v2:10:3
        cart:v2:10:5
        cart:v2:10:7

    All of them are deleted.
    """

    redis_client = get_redis()

    pattern = (
        f"cart:v2:{user_id}:*"
    )

    async for key in redis_client.scan_iter(
        match=pattern
    ):
        await redis_client.delete(key)