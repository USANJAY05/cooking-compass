from collections import defaultdict
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


async def get_cart_service(
    days: int,
    current_user: dict,
    db: AsyncSession,
) -> CartResponse:

    user_id = current_user["id"]

    redis_client = get_redis()

    # Use v2 because the cached response structure changed
    cache_key = f"cart:v2:{user_id}:{days}"

    # =====================================================
    # 1. Check Redis
    # =====================================================

    cached_cart = await redis_client.get(cache_key)

    if cached_cart:
        return CartResponse.model_validate_json(cached_cart)

    # =====================================================
    # 2. Get active routines
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
            )
        )
    )

    routines = result.scalars().unique().all()

    # =====================================================
    # 3. Aggregate ingredients
    # =====================================================

    ingredient_quantities: dict[int, Decimal] = defaultdict(
        lambda: Decimal("0")
    )

    ingredient_units: dict[int, str] = {}

    ingredient_names: dict[int, str] = {}

    for routine in routines:

        for routine_item in routine.items:

            recipe = routine_item.recipe

            if recipe is None:
                continue

            # -------------------------------------------------
            # SERVING
            # -------------------------------------------------

            if routine_item.quantity_type == "SERVING":

                if recipe.servings <= 0:
                    continue

                multiplier = (
                    routine_item.quantity
                    / recipe.servings
                )

            # -------------------------------------------------
            # Other quantity types
            # -------------------------------------------------

            else:

                total_recipe_quantity = Decimal("0")

                for recipe_ingredient in recipe.ingredients:

                    if (
                        recipe_ingredient.unit.upper()
                        == routine_item.quantity_type.upper()
                    ):
                        total_recipe_quantity += (
                            recipe_ingredient.quantity
                        )

                if total_recipe_quantity <= 0:
                    continue

                multiplier = (
                    routine_item.quantity
                    / total_recipe_quantity
                )

            # -------------------------------------------------
            # Add recipe ingredients
            # -------------------------------------------------

            for recipe_ingredient in recipe.ingredients:

                ingredient_id = (
                    recipe_ingredient.ingredient_id
                )

                calculated_quantity = (
                    recipe_ingredient.quantity
                    * multiplier
                )

                ingredient_quantities[ingredient_id] += (
                    calculated_quantity
                )

                ingredient_units[ingredient_id] = (
                    recipe_ingredient.unit
                )

                # -------------------------------------------------
                # Store ingredient name
                # -------------------------------------------------

                if recipe_ingredient.ingredient is not None:
                    ingredient_names[ingredient_id] = (
                        recipe_ingredient.ingredient.name
                    )

    # =====================================================
    # 4. Build response
    # =====================================================

    cart_items = [
        CartItemResponse(
            ingredient_id=ingredient_id,
            name=ingredient_names.get(ingredient_id),
            quantity=quantity,
            unit=ingredient_units[ingredient_id],
        )
        for ingredient_id, quantity
        in ingredient_quantities.items()
    ]

    response = CartResponse(
        items=cart_items,
    )

    # =====================================================
    # 5. Save to Redis
    # =====================================================

    await redis_client.set(
        cache_key,
        response.model_dump_json(),
        ex=CART_TTL,
    )

    return response




# =========================================================
# Add this function to the SAME FILE that contains
# get_cart_service (e.g. cooking_compass/services/cart/...)
# =========================================================

async def invalidate_cart_cache(user_id: int) -> None:
    """
    Deletes all cached cart entries for a user.

    Cart cache keys look like: cart:v2:{user_id}:{days}
    Since `days` varies per request, we don't know every
    cached variant for this user, so we scan and delete
    by pattern instead of a single key.

    Call this any time something that feeds cart
    calculation changes for a user — e.g. routine
    created/updated/deleted, routine items changed, etc.
    """

    redis_client = get_redis()

    pattern = f"cart:v2:{user_id}:*"

    async for key in redis_client.scan_iter(match=pattern):
        await redis_client.delete(key)