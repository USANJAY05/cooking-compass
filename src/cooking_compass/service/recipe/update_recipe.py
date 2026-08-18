from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from cooking_compass.core.db import SessionLocal
from cooking_compass.models.recipe import Recipe
from cooking_compass.models.recipe_categories import RecipeCategory
from cooking_compass.models.recipe_ingredients import RecipeIngredient
from cooking_compass.models.recipe_instructions import RecipeInstruction
from cooking_compass.models.recipe_tags import RecipeTag
from cooking_compass.models.tags import Tag


async def _get_or_create_tag_ids(
    session,
    tag_names: list[str],
) -> list[int]:
    # normalize: strip whitespace, lowercase, dedupe while preserving order
    seen = set()
    normalized = []

    for name in tag_names:
        clean = name.strip().lower()

        if clean and clean not in seen:
            seen.add(clean)
            normalized.append(clean)

    if not normalized:
        return []

    result = await session.execute(
        select(Tag).where(Tag.name.in_(normalized))
    )

    existing = {
        tag.name: tag.id
        for tag in result.scalars().all()
    }

    missing = [
        name
        for name in normalized
        if name not in existing
    ]

    for name in missing:
        try:
            async with session.begin_nested():
                tag = Tag(name=name)
                session.add(tag)
                await session.flush()

            existing[name] = tag.id

        except IntegrityError:
            # Another transaction created the tag
            result = await session.execute(
                select(Tag).where(Tag.name == name)
            )

            tag = result.scalar_one()
            existing[name] = tag.id

    return [
        existing[name]
        for name in normalized
    ]


async def update_recipe_service(
    recipe_id: int,
    request,
    current_user: dict,
):
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
            # -----------------------------------------
            # 1. Get existing recipe
            # -----------------------------------------

            result = await session.execute(
                select(Recipe).where(
                    Recipe.id == recipe_id,
                    Recipe.user_id == current_user["id"],
                )
            )

            recipe = result.scalar_one_or_none()

            if recipe is None:
                return None

            # -----------------------------------------
            # 2. Update recipe fields
            # -----------------------------------------

            for field, value in recipe_data.items():
                setattr(recipe, field, value)

            await session.flush()

            # -----------------------------------------
            # 3. Delete existing categories
            # -----------------------------------------

            await session.execute(
                delete(RecipeCategory).where(
                    RecipeCategory.recipe_id == recipe.id
                )
            )

            # Add new categories

            session.add_all(
                RecipeCategory(
                    recipe_id=recipe.id,
                    category_id=category_id,
                )
                for category_id in request.category_ids
            )

            # -----------------------------------------
            # 4. Delete existing ingredients
            # -----------------------------------------

            await session.execute(
                delete(RecipeIngredient).where(
                    RecipeIngredient.recipe_id == recipe.id
                )
            )

            # Add new ingredients

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

            # -----------------------------------------
            # 5. Delete existing instructions
            # -----------------------------------------

            await session.execute(
                delete(RecipeInstruction).where(
                    RecipeInstruction.recipe_id == recipe.id
                )
            )

            # Add new instructions

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

            # -----------------------------------------
            # 6. Delete existing tags
            # -----------------------------------------

            await session.execute(
                delete(RecipeTag).where(
                    RecipeTag.recipe_id == recipe.id
                )
            )

            # Get/create tags

            tag_ids = await _get_or_create_tag_ids(
                session,
                request.tag_names,
            )

            # Add new tags

            session.add_all(
                RecipeTag(
                    recipe_id=recipe.id,
                    tag_id=tag_id,
                )
                for tag_id in tag_ids
            )

            # -----------------------------------------
            # 7. image_urls
            # -----------------------------------------
            # Still excluded because upload flow isn't wired yet.

            # -----------------------------------------
            # 8. Commit
            # -----------------------------------------

            await session.commit()

            await session.refresh(recipe)

            return recipe

        except Exception:
            await session.rollback()
            raise