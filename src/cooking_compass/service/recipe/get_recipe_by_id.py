from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from cooking_compass.core.db import SessionLocal

from cooking_compass.models.recipe import Recipe
from cooking_compass.models.recipe_images import RecipeImage
from cooking_compass.models.recipe_ratings import RecipeRating
from cooking_compass.models.recipe_nutrition import RecipeNutrition
from cooking_compass.models.recipe_ingredients import RecipeIngredient


async def get_recipe_by_id_service(
    recipe_id: int,
    current_user: dict,
):
    async with SessionLocal() as session:

        # --------------------------------------------------
        # Get recipe
        # --------------------------------------------------
        query = (
            select(Recipe)
            .where(
                Recipe.id == recipe_id,
                Recipe.deleted_at.is_(None),
            )
            .options(
                # Ingredients
                selectinload(
                    Recipe.ingredients
                ).selectinload(
                    RecipeIngredient.ingredient
                ),

                # Instructions
                selectinload(
                    Recipe.instructions
                ),

                # Categories
                selectinload(
                    Recipe.categories
                ),

                # Tags
                selectinload(
                    Recipe.tags
                ),

                # Images
                selectinload(
                    Recipe.images
                ).selectinload(
                    RecipeImage.image
                ),

                # Nutrition
                selectinload(
                    Recipe.nutrition
                ).selectinload(
                    RecipeNutrition.nutrient
                ),

                # Ratings
                selectinload(
                    Recipe.ratings
                ),
            )
        )

        result = await session.execute(query)

        recipe = result.scalar_one_or_none()

        # --------------------------------------------------
        # Recipe not found
        # --------------------------------------------------
        if recipe is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "message": "Recipe not found",
                },
            )

        # --------------------------------------------------
        # Check access
        # --------------------------------------------------
        print(current_user)
        is_owner = (
            recipe.user_id == current_user.get("id")
            

        )

        if not is_owner:
            print("hiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii")

            if (
                recipe.visibility != "PUBLIC"
            ):
                raise HTTPException(
                    status_code=404,
                    detail={
                        "success": False,
                        "message": "Recipe not found",
                    },
                )

        # --------------------------------------------------
        # Ingredients
        # --------------------------------------------------
        ingredients = [
            {
                "ingredient_id": item.ingredient_id,
                "quantity": item.quantity,
                "unit": item.unit,
                "display_order": item.display_order,
            }
            for item in sorted(
                recipe.ingredients,
                key=lambda x: x.display_order,
            )
        ]

        # --------------------------------------------------
        # Instructions
        # --------------------------------------------------
        instructions = [
            {
                "step_number": item.step_number,
                "instruction_text": item.instruction_text,
                "timer_seconds": item.timer_seconds,
                "tip": item.tip,
                "reference_recipe_id": item.reference_recipe_id,
            }
            for item in sorted(
                recipe.instructions,
                key=lambda x: x.step_number,
            )
        ]

        # --------------------------------------------------
        # Categories
        # --------------------------------------------------
        category_ids = [
            item.category_id
            for item in recipe.categories
        ]

        # --------------------------------------------------
        # Tags
        # --------------------------------------------------
        tag_ids = [
            item.tag_id
            for item in recipe.tags
        ]

        # --------------------------------------------------
        # Images
        # --------------------------------------------------
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

        # --------------------------------------------------
        # Nutrition
        # --------------------------------------------------
        nutrition_items = []

        for item in recipe.nutrition:

            if item.nutrient is None:
                continue

            nutrition_items.append(
                {
                    "code": item.nutrient.code,
                    "amount": float(
                        item.amount_per_serving
                    ),
                    "unit": item.nutrient.unit,
                }
            )

        nutrition = None

        if nutrition_items:

            nutrition = {
                "servings": int(recipe.servings),
                "items": nutrition_items,
            }

        # --------------------------------------------------
        # Rating
        # --------------------------------------------------
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
            ).where(
                RecipeRating.recipe_id == recipe.id
            )
        )

        average, count = rating_result.one()

        rating = {
            "average": float(
                average or 0
            ),
            "count": count,
        }

        # --------------------------------------------------
        # Final response
        # --------------------------------------------------
        return {
            "id": recipe.id,
            "name": recipe.name,
            "description": recipe.description,
            "preparation_time": recipe.preparation_time,
            "cooking_time": recipe.cooking_time,
            "total_time": recipe.total_time,
            "servings": int(recipe.servings),
            "visibility": recipe.visibility,

            "image_urls": image_urls,

            "ingredients": ingredients,

            "instructions": instructions,

            "category_ids": category_ids,

            "tag_ids": tag_ids,

            "nutrition": nutrition,

            "rating": rating,
        }