from sqlalchemy import select

from cooking_compass.core.db import SessionLocal
from cooking_compass.models.recipe import Recipe
from cooking_compass.models.recipe_categories import RecipeCategory
from cooking_compass.models.recipe_ingredients import RecipeIngredient
from cooking_compass.models.recipe_instructions import RecipeInstruction
from cooking_compass.models.recipe_tags import RecipeTag
from cooking_compass.models.tags import Tag


async def _get_or_create_tag_ids(session, tag_names: list[str]) -> list[int]:
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

    result = await session.execute(select(Tag).where(Tag.name.in_(normalized)))
    existing = {tag.name: tag.id for tag in result.scalars().all()}

    missing = [name for name in normalized if name not in existing]

    for name in missing:
        tag = Tag(name=name)
        session.add(tag)
        try:
            await session.flush()  # assigns tag.id, catches unique-constraint races
        except IntegrityError:
            await session.rollback()
            # someone else created it concurrently — fetch it
            result = await session.execute(select(Tag).where(Tag.name == name))
            tag = result.scalars().first()
        existing[name] = tag.id

    return [existing[name] for name in normalized]


async def create_recipe_service(request, current_user: dict):
    recipe_data = request.model_dump(
        exclude={"ingredients", "instructions", "category_ids", "tag_names", "image_urls"}
    )

    async with SessionLocal() as session:
        try:
            recipe = Recipe(**recipe_data, user_id=current_user["id"])
            session.add(recipe)
            await session.flush()  # populates recipe.id

            session.add_all(
                RecipeCategory(recipe_id=recipe.id, category_id=cat_id)
                for cat_id in request.category_ids
            )

            session.add_all(
                RecipeIngredient(
                    recipe_id=recipe.id,
                    ingredient_id=ing.ingredient_id,
                    quantity=ing.quantity,
                    unit=ing.unit,
                    display_order=ing.display_order,
                )
                for ing in request.ingredients
            )

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

            tag_ids = await _get_or_create_tag_ids(session, request.tag_names)
            session.add_all(
                RecipeTag(recipe_id=recipe.id, tag_id=tag_id)
                for tag_id in tag_ids
            )

            # image_urls — still excluded, no upload flow wired yet

            await session.commit()
            await session.refresh(recipe)
            return recipe

        except Exception:
            await session.rollback()
            raise