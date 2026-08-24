from collections import defaultdict

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


async def get_recipe_by_id_service(
    recipe_id: int,
    current_user: dict,
):
    async with SessionLocal() as session:

        # =========================================================
        # 1. Get recipe
        # =========================================================

        query = (
            select(Recipe)
            .where(
                Recipe.id == recipe_id,
                Recipe.deleted_at.is_(None),
            )
            .options(

                # -------------------------------------------------
                # Ingredients
                #
                # Recipe
                #   -> RecipeIngredient
                #       -> Ingredient
                #           -> IngredientNutrient
                #               -> Nutrient
                # -------------------------------------------------

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

                # -------------------------------------------------
                # Instructions
                #   -> Images
                #       -> Image
                # -------------------------------------------------

                selectinload(
                    Recipe.instructions
                )
                .selectinload(
                    RecipeInstruction.images
                )
                .selectinload(
                    InstructionImage.image
                ),

                # -------------------------------------------------
                # Categories
                # -------------------------------------------------

                selectinload(
                    Recipe.categories
                ),

                # -------------------------------------------------
                # Tags
                # -------------------------------------------------

                selectinload(
                    Recipe.tags
                ),

                # -------------------------------------------------
                # Recipe Images
                #   -> Image
                # -------------------------------------------------

                selectinload(
                    Recipe.images
                )
                .selectinload(
                    RecipeImage.image
                ),

                # -------------------------------------------------
                # Ratings
                # -------------------------------------------------

                selectinload(
                    Recipe.ratings
                ),
            )
        )

        result = await session.execute(query)

        recipe = result.scalar_one_or_none()

        # =========================================================
        # 2. Recipe not found
        # =========================================================

        if recipe is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "message": "Recipe not found",
                },
            )

        # =========================================================
        # 3. Check access
        # =========================================================

        user_id = current_user.get("id")

        is_owner = recipe.user_id == user_id

        if not is_owner and recipe.visibility != "PUBLIC":
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "message": "Recipe not found",
                },
            )

        # =========================================================
        # 4. Ingredients
        # =========================================================

        ingredients = []

        for item in sorted(
            recipe.ingredients,
            key=lambda x: x.display_order,
        ):

            ingredient_name = None

            if item.ingredient is not None:
                ingredient_name = item.ingredient.name

            ingredients.append(
                {
                    "ingredient_id": item.ingredient_id,
                    "name": ingredient_name,
                    "quantity": float(item.quantity),
                    "unit": item.unit,
                    "display_order": item.display_order,
                }
            )

        # =========================================================
        # 5. Instructions
        # =========================================================

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

                if instruction_image.image is None:
                    continue

                storage_key = (
                    instruction_image.image.storage_key
                )

                if storage_key.startswith(
                    ("http://", "https://")
                ):
                    reference_image = storage_key
                    break

            instructions.append(
                {
                    "step_number": item.step_number,
                    "instruction_text": item.instruction_text,
                    "timer_seconds": item.timer_seconds,
                    "tip": item.tip,
                    "reference_recipe_id": (
                        item.reference_recipe_id
                    ),
                    "reference_image": reference_image,
                }
            )

        # =========================================================
        # 6. Categories
        # =========================================================

        category_ids = [
            item.category_id
            for item in recipe.categories
        ]

        # =========================================================
        # 7. Tags
        # =========================================================

        tag_ids = [
            item.tag_id
            for item in recipe.tags
        ]

        # =========================================================
        # 8. Recipe Images
        # =========================================================

        image_urls = []

        for recipe_image in sorted(
            recipe.images,
            key=lambda x: x.display_order,
        ):

            if recipe_image.image is None:
                continue

            storage_key = (
                recipe_image.image.storage_key
            )

            if storage_key.startswith(
                ("http://", "https://")
            ):
                image_urls.append(storage_key)

        # =========================================================
        # 9. Nutrition
        # =========================================================

        nutrition_totals = defaultdict(float)
        nutrition_units = {}
        nutrition_names = {}

        for recipe_ingredient in recipe.ingredients:

            ingredient = recipe_ingredient.ingredient

            if ingredient is None:
                continue

            # -----------------------------------------------------
            # IngredientNutrient.amount_per_100g is based on 100g.
            #
            # Therefore this calculation is directly valid when
            # the recipe ingredient quantity is expressed in grams.
            # -----------------------------------------------------

            unit = (
                recipe_ingredient.unit
                .strip()
                .lower()
            )

            if unit not in {
                "g",
                "gram",
                "grams",
            }:
                continue

            ingredient_quantity = float(
                recipe_ingredient.quantity
            )

            # -----------------------------------------------------
            # Ingredient
            #     -> nutrients
            #         -> nutrient
            # -----------------------------------------------------

            for ingredient_nutrient in ingredient.nutrients:

                nutrient = (
                    ingredient_nutrient.nutrient
                )

                if nutrient is None:
                    continue

                nutrient_code = nutrient.code

                amount_per_100g = float(
                    ingredient_nutrient.amount_per_100g
                )

                # -------------------------------------------------
                # Calculate nutrition for this ingredient.
                #
                # Example:
                #
                # 200g ingredient
                # 50 kcal / 100g
                #
                # 50 * 200 / 100 = 100 kcal
                # -------------------------------------------------

                calculated_amount = (
                    amount_per_100g
                    * ingredient_quantity
                    / 100
                )

                nutrition_totals[
                    nutrient_code
                ] += calculated_amount

                nutrition_units[
                    nutrient_code
                ] = nutrient.unit

                nutrition_names[
                    nutrient_code
                ] = nutrient.name

        # =========================================================
        # 10. Convert total nutrition to per serving
        # =========================================================

        servings = int(recipe.servings)

        nutrition_items = []

        if servings > 0:

            for (
                nutrient_code,
                total_amount,
            ) in nutrition_totals.items():

                amount_per_serving = (
                    total_amount / servings
                )

                nutrition_items.append(
                    {
                        "code": nutrient_code,
                        "name": nutrition_names[
                            nutrient_code
                        ],
                        "amount": round(
                            amount_per_serving,
                            2,
                        ),
                        "unit": nutrition_units[
                            nutrient_code
                        ],
                    }
                )

        # Consistent ordering
        nutrition_items.sort(
            key=lambda x: x["code"]
        )

        nutrition = {
            "servings": servings,
            "items": nutrition_items,
        }

        # =========================================================
        # 11. Rating
        # =========================================================

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
                RecipeRating.recipe_id == recipe.id
            )
        )

        average, count = rating_result.one()

        rating = {
            "average": float(
                average or 0
            ),
            "count": int(count),
        }

        # =========================================================
        # 12. Final response
        # =========================================================

        return {
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

            "visibility": recipe.visibility,

            "image_urls": image_urls,

            "ingredients": ingredients,

            "instructions": instructions,

            "category_ids": category_ids,

            "tag_ids": tag_ids,

            "nutrition": nutrition,

            "rating": rating,
        }