from collections import defaultdict
from decimal import Decimal, InvalidOperation

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from cooking_compass.core.db import SessionLocal

from cooking_compass.models.recipe import Recipe
from cooking_compass.models.recipe_ingredients import RecipeIngredient
from cooking_compass.models.ingredients import Ingredient
from cooking_compass.models.ingredient_nutrients import IngredientNutrient
from cooking_compass.models.recipe_instructions import RecipeInstruction
from cooking_compass.models.instruction_images import InstructionImage
from cooking_compass.models.recipe_images import RecipeImage
from cooking_compass.models.recipe_ratings import RecipeRating

from cooking_compass.utils.cache import (
    CacheNamespace,
    build_cache_key_from_data,
    cache_get,
    cache_set,
)


def to_decimal(
    value,
    default=Decimal("0"),
) -> Decimal:
    """
    Safely convert a value to Decimal.
    """

    if value is None:
        return default

    if isinstance(value, Decimal):
        return value

    try:
        return Decimal(str(value))

    except (
        InvalidOperation,
        ValueError,
        TypeError,
    ):
        return default


async def get_recipe_by_id_service(
    recipe_id: int,
    current_user: dict,
):

    # ==========================================================
    # Cache key
    # ==========================================================
    #
    # We don't know whether the recipe is PUBLIC until we
    # query the database.
    #
    # Therefore we include the current user ID in the cache key.
    #
    # This is the safest approach because:
    #
    # - Owner can see their own private recipe.
    # - Another user cannot receive the owner's cached response.
    # - Public recipes are still cached.
    #
    # ==========================================================

    current_user_id = current_user.get("id")

    cache_key = await build_cache_key_from_data(
        CacheNamespace.RECIPES,
        {
            "type": "detail",
            "recipe_id": recipe_id,
            "current_user_id": current_user_id,
        },
    )

    # ==========================================================
    # Cache lookup
    # ==========================================================

    cached_result = await cache_get(
        cache_key
    )

    if cached_result is not None:
        return cached_result

    # ==========================================================
    # Database
    # ==========================================================

    async with SessionLocal() as session:

        # ======================================================
        # 1. Load Recipe
        # ======================================================

        query = (
            select(Recipe)
            .where(
                Recipe.id == recipe_id,
                Recipe.deleted_at.is_(None),
            )
            .options(

                selectinload(
                    Recipe.ingredients
                )
                .selectinload(
                    RecipeIngredient.ingredient
                )
                .selectinload(
                    Ingredient.nutrients
                )
                .selectinload(
                    IngredientNutrient.nutrient
                ),

                selectinload(
                    Recipe.instructions
                )
                .selectinload(
                    RecipeInstruction.images
                )
                .selectinload(
                    InstructionImage.image
                ),

                selectinload(
                    Recipe.categories
                ),

                selectinload(
                    Recipe.tags
                ),

                selectinload(
                    Recipe.images
                )
                .selectinload(
                    RecipeImage.image
                ),

                selectinload(
                    Recipe.ratings
                ),
            )
        )

        result = await session.execute(
            query
        )

        recipe = result.scalar_one_or_none()

        # ======================================================
        # 2. Recipe Not Found
        # ======================================================

        if recipe is None:

            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "message": "Recipe not found",
                },
            )

        # ======================================================
        # 3. Access Check
        # ======================================================

        user_id = current_user.get("id")

        is_owner = (
            recipe.user_id == user_id
        )

        if (
            not is_owner
            and recipe.visibility != "PUBLIC"
        ):

            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "message": "Recipe not found",
                },
            )

        # ======================================================
        # 4. Ingredients
        # ======================================================

        ingredients = []

        for item in sorted(
            recipe.ingredients,
            key=lambda x: x.display_order,
        ):

            ingredient_name = None

            if item.ingredient is not None:

                ingredient_name = (
                    item.ingredient.name
                )

            ingredients.append(
                {
                    "ingredient_id": (
                        item.ingredient_id
                    ),

                    "name": ingredient_name,

                    "quantity": float(
                        to_decimal(
                            item.quantity
                        )
                    ),

                    "unit": item.unit,

                    "display_order": (
                        item.display_order
                    ),
                }
            )

        # ======================================================
        # 5. Instructions
        # ======================================================

        instructions = []

        for item in sorted(
            recipe.instructions,
            key=lambda x: x.step_number,
        ):

            reference_image = None

            sorted_images = sorted(
                item.images,
                key=lambda x: x.display_order,
            )

            for instruction_image in sorted_images:

                if (
                    instruction_image.image
                    is None
                ):
                    continue

                storage_key = (
                    instruction_image
                    .image
                    .storage_key
                )

                if storage_key.startswith(
                    (
                        "http://",
                        "https://",
                    )
                ):

                    reference_image = (
                        storage_key
                    )

                    break

            instructions.append(
                {
                    "step_number": (
                        item.step_number
                    ),

                    "instruction_text": (
                        item.instruction_text
                    ),

                    "timer_seconds": (
                        item.timer_seconds
                    ),

                    "tip": item.tip,

                    "reference_recipe_id": (
                        item.reference_recipe_id
                    ),

                    "reference_image": (
                        reference_image
                    ),
                }
            )

        # ======================================================
        # 6. Categories
        # ======================================================

        category_ids = [
            item.category_id
            for item in recipe.categories
        ]

        # ======================================================
        # 7. Tags
        # ======================================================

        tag_ids = [
            item.tag_id
            for item in recipe.tags
        ]

        # ======================================================
        # 8. Recipe Images
        # ======================================================

        image_urls = []

        for recipe_image in sorted(
            recipe.images,
            key=lambda x: x.display_order,
        ):

            if (
                recipe_image.image
                is None
            ):
                continue

            storage_key = (
                recipe_image
                .image
                .storage_key
            )

            if storage_key.startswith(
                (
                    "http://",
                    "https://",
                )
            ):

                image_urls.append(
                    storage_key
                )

        # ======================================================
        # 9. Nutrition
        # ======================================================

        nutrition_totals = defaultdict(
            lambda: Decimal("0")
        )

        nutrition_units = {}
        nutrition_names = {}
        nutrition_types = {}

        for recipe_ingredient in (
            recipe.ingredients
        ):

            ingredient = (
                recipe_ingredient
                .ingredient
            )

            if ingredient is None:
                continue

            # --------------------------------------------------
            # Normalize Unit
            # --------------------------------------------------

            unit = (
                recipe_ingredient.unit
                .strip()
                .lower()
            )

            # --------------------------------------------------
            # Only calculate gram quantities
            # --------------------------------------------------

            if unit not in {
                "g",
                "gram",
                "grams",
            }:
                continue

            ingredient_quantity = (
                to_decimal(
                    recipe_ingredient.quantity
                )
            )

            if ingredient_quantity <= 0:
                continue

            # --------------------------------------------------
            # Nutrients
            # --------------------------------------------------

            for ingredient_nutrient in (
                ingredient.nutrients
            ):

                nutrient = (
                    ingredient_nutrient
                    .nutrient
                )

                if nutrient is None:
                    continue

                nutrient_code = (
                    nutrient.code
                )

                amount_per_100g = (
                    to_decimal(
                        ingredient_nutrient
                        .amount_per_100g
                    )
                )

                # ------------------------------------------------
                # Calculate nutrient amount
                # ------------------------------------------------

                calculated_amount = (
                    amount_per_100g
                    * ingredient_quantity
                    / Decimal("100")
                )

                nutrition_totals[
                    nutrient_code
                ] += calculated_amount

                # ------------------------------------------------
                # Store nutrient metadata
                # ------------------------------------------------

                nutrition_units[
                    nutrient_code
                ] = nutrient.unit

                nutrition_names[
                    nutrient_code
                ] = nutrient.name

                nutrition_types[
                    nutrient_code
                ] = nutrient.nutrition_type

        # ======================================================
        # 10. Nutrition Per Serving
        # ======================================================

        servings = recipe.servings

        nutrition = None

        if servings is not None:

            servings_decimal = to_decimal(
                servings
            )

            if servings_decimal > 0:

                nutrition_items = []

                for (
                    nutrient_code,
                    total_amount,
                ) in nutrition_totals.items():

                    amount_per_serving = (
                        total_amount
                        / servings_decimal
                    )

                    # --------------------------------------------
                    # Round FIRST
                    # --------------------------------------------

                    rounded_amount = round(
                        amount_per_serving,
                        2,
                    )

                    # --------------------------------------------
                    # Skip zero values
                    # --------------------------------------------

                    if rounded_amount <= 0:
                        continue

                    nutrition_items.append(
                        {
                            "code": nutrient_code,

                            "name": (
                                nutrition_names[
                                    nutrient_code
                                ]
                            ),

                            "amount": float(
                                rounded_amount
                            ),

                            "unit": (
                                nutrition_units[
                                    nutrient_code
                                ]
                            ),

                            "type": (
                                nutrition_types[
                                    nutrient_code
                                ]
                            ),
                        }
                    )

                # --------------------------------------------
                # Sort nutrients by code
                # --------------------------------------------

                nutrition_items.sort(
                    key=lambda item: item["code"]
                )

                nutrition = {
                    "servings": servings,
                    "items": nutrition_items,
                }

        # ======================================================
        # 11. Rating
        # ======================================================

        rating_result = await session.execute(
            select(
                func.coalesce(
                    func.avg(
                        RecipeRating.rating
                    ),
                    0,
                ),
                func.count(
                    RecipeRating.id
                ),
            )
            .where(
                RecipeRating.recipe_id
                == recipe.id
            )
        )

        average, count = (
            rating_result.one()
        )

        rating = {
            "average": float(
                average or 0
            ),
            "count": int(
                count
            ),
        }

        # ======================================================
        # 12. Cooked Weight
        # ======================================================

        cooked_weight_amount = None

        if (
            recipe.cooked_weight_amount
            is not None
        ):

            cooked_weight_amount = float(
                recipe.cooked_weight_amount
            )

        cooked_weight_unit = (
            recipe.cooked_weight_unit
            if recipe.cooked_weight_unit
            is not None
            else None
        )

        # ======================================================
        # 13. Cooked Weight Per Serving
        # ======================================================

        cooked_weight_per_serving = None

        if (
            recipe.cooked_weight_amount
            is not None
            and servings is not None
        ):

            cooked_weight_decimal = (
                to_decimal(
                    recipe.cooked_weight_amount
                )
            )

            servings_decimal = (
                to_decimal(
                    servings
                )
            )

            if (
                cooked_weight_decimal > 0
                and servings_decimal > 0
            ):

                cooked_weight_per_serving = (
                    cooked_weight_decimal
                    / servings_decimal
                )

        # ======================================================
        # 14. Final Response
        # ======================================================

        response = {
            "id": recipe.id,

            "name": recipe.name,

            "description": recipe.description,

            "preparation_time": (
                recipe.preparation_time
            ),

            "cooking_time": (
                recipe.cooking_time
            ),

            "total_time": (
                recipe.total_time
            ),

            "servings": servings,

            "cooked_weight_amount": (
                cooked_weight_amount
            ),

            "cooked_weight_unit": (
                cooked_weight_unit
            ),

            "visibility": (
                recipe.visibility
            ),

            "image_urls": image_urls,

            "ingredients": ingredients,

            "instructions": instructions,

            "category_ids": category_ids,

            "tag_ids": tag_ids,

            "nutrition": nutrition,

            "rating": rating,
        }

    # ==========================================================
    # Cache response
    # ==========================================================

    await cache_set(
        cache_key,
        response,
        ttl=300,
    )

    return response
