from fastapi import HTTPException
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from cooking_compass.core.db import SessionLocal
from cooking_compass.models.recipe import Recipe
from cooking_compass.models.recipe_categories import RecipeCategory
from cooking_compass.models.recipe_ingredients import RecipeIngredient
from cooking_compass.models.recipe_instructions import RecipeInstruction
from cooking_compass.models.recipe_tags import RecipeTag

from cooking_compass.service.recipe.create_recipe import _get_or_create_tag_ids
from cooking_compass.schema.recipe.response_schema import RecipeDetailResponse


async def update_recipe_service(
    recipe_id: int,
    request,
    current_user: dict,
):
    """
    Full-replace update of a recipe and all related records.

    Rating and nutrition are never written here — they're read-only
    in this response (populated by their own endpoints later).
    """

    recipe_data = request.model_dump(
        exclude={
            "ingredients",
            "instructions",
            "category_ids",
            "tag_names",
            "image_urls",
        }
    )

    async with SessionLocal() as session:
        try:
            # ---------------------------------------------------------
            # 1. Fetch and authorize
            # ---------------------------------------------------------

            result = await session.execute(
                select(Recipe).where(Recipe.id == recipe_id)
            )

            recipe = result.scalars().first()

            if recipe is None:
                raise HTTPException(
                    status_code=404,
                    detail="Recipe not found",
                )

            if recipe.user_id != current_user["id"]:
                raise HTTPException(
                    status_code=403,
                    detail="Not your recipe",
                )

            # ---------------------------------------------------------
            # 2. Update scalar fields
            # ---------------------------------------------------------

            for field, value in recipe_data.items():
                setattr(recipe, field, value)

            # ---------------------------------------------------------
            # 3. Clear existing child rows
            # ---------------------------------------------------------

            await session.execute(
                delete(RecipeCategory).where(
                    RecipeCategory.recipe_id == recipe.id
                )
            )

            await session.execute(
                delete(RecipeIngredient).where(
                    RecipeIngredient.recipe_id == recipe.id
                )
            )

            await session.execute(
                delete(RecipeInstruction).where(
                    RecipeInstruction.recipe_id == recipe.id
                )
            )

            await session.execute(
                delete(RecipeTag).where(
                    RecipeTag.recipe_id == recipe.id
                )
            )

            # ---------------------------------------------------------
            # 4. Recreate categories
            # ---------------------------------------------------------

            if request.category_ids:
                session.add_all(
                    RecipeCategory(
                        recipe_id=recipe.id,
                        category_id=category_id,
                    )
                    for category_id in request.category_ids
                )

            # ---------------------------------------------------------
            # 5. Recreate ingredients
            # ---------------------------------------------------------

            if request.ingredients:
                session.add_all(
                    RecipeIngredient(
                        recipe_id=recipe.id,
                        ingredient_id=ingredient.ingredient_id,
                        quantity=ingredient.quantity,
                        unit=ingredient.unit,
                        display_order=ingredient.display_order,
                    )
                    for ingredient in request.ingredients
                )

            # ---------------------------------------------------------
            # 6. Recreate instructions
            # ---------------------------------------------------------

            if request.instructions:
                session.add_all(
                    RecipeInstruction(
                        recipe_id=recipe.id,
                        step_number=step.step_number,
                        instruction_text=step.instruction_text,
                        timer_seconds=step.timer_seconds,
                        tip=step.tip,
                        reference_recipe_id=step.reference_recipe_id,
                    )
                    for step in request.instructions
                )

            # ---------------------------------------------------------
            # 7. Get/create tags and recreate recipe-tag links
            # ---------------------------------------------------------

            tag_ids = await _get_or_create_tag_ids(
                session,
                request.tag_names,
            )

            if tag_ids:
                session.add_all(
                    RecipeTag(
                        recipe_id=recipe.id,
                        tag_id=tag_id,
                    )
                    for tag_id in tag_ids
                )

            # ---------------------------------------------------------
            # 8. Image URLs
            # ---------------------------------------------------------

            # TODO:
            # Persist image URLs once image persistence is implemented.

            # ---------------------------------------------------------
            # 9. Commit
            # ---------------------------------------------------------

            await session.commit()

            # ---------------------------------------------------------
            # 10. Re-fetch recipe with all required relationships
            # ---------------------------------------------------------

            result = await session.execute(
                select(Recipe)
                .where(Recipe.id == recipe.id)
                .options(
                    # RecipeIngredient -> Ingredient
                    selectinload(Recipe.ingredients).selectinload(
                        RecipeIngredient.ingredient
                    ),

                    # Recipe -> instructions
                    selectinload(Recipe.instructions),

                    # Recipe -> categories
                    selectinload(Recipe.categories),

                    # Recipe -> tags
                    selectinload(Recipe.tags),
                )
            )

            recipe = result.scalars().first()

            if recipe is None:
                raise HTTPException(
                    status_code=404,
                    detail="Recipe not found after update",
                )

            # ---------------------------------------------------------
            # 11. Build ingredient response objects
            # ---------------------------------------------------------
            #
            # IMPORTANT:
            #
            # recipe.ingredients contains RecipeIngredient ORM objects.
            #
            # RecipeDetailResponse expects an ingredient with `name`,
            # but RecipeIngredient normally contains `ingredient_id`.
            #
            # The actual name comes from:
            #
            #     recipe_ingredient.ingredient.name
            #
            # So we explicitly map the ORM objects here.
            # ---------------------------------------------------------

            ingredients_response = [
                {
                    "ingredient_id": recipe_ingredient.ingredient_id,
                    "name": recipe_ingredient.ingredient.name,
                    "quantity": recipe_ingredient.quantity,
                    "unit": recipe_ingredient.unit,
                    "display_order": recipe_ingredient.display_order,
                }
                for recipe_ingredient in recipe.ingredients
            ]

            # ---------------------------------------------------------
            # 12. Build instructions response
            # ---------------------------------------------------------

            instructions_response = [
                {
                    "step_number": instruction.step_number,
                    "instruction_text": instruction.instruction_text,
                    "timer_seconds": instruction.timer_seconds,
                    "tip": instruction.tip,
                    "reference_recipe_id": instruction.reference_recipe_id,
                }
                for instruction in recipe.instructions
            ]

            # ---------------------------------------------------------
            # 13. Build final response
            # ---------------------------------------------------------

            response_data = {
                "id": recipe.id,
                "name": recipe.name,
                "description": recipe.description,
                "preparation_time": recipe.preparation_time,
                "cooking_time": recipe.cooking_time,
                "total_time": recipe.total_time,
                "servings": recipe.servings,
                "visibility": recipe.visibility,
                "image_urls": [],

                "ingredients": ingredients_response,

                "instructions": instructions_response,

                "category_ids": [
                    category.category_id
                    for category in recipe.categories
                ],

                "tag_ids": [
                    tag.tag_id
                    for tag in recipe.tags
                ],
            }

            return RecipeDetailResponse.model_validate(response_data)

        except HTTPException:
            await session.rollback()
            raise

        except Exception:
            await session.rollback()
            raise
