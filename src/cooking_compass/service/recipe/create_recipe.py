from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from cooking_compass.core.db import SessionLocal
from cooking_compass.schema.recipe.components_schema import to_grams
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
    """
    Get existing tag IDs and create missing tags.

    Tag names are:
    - stripped
    - converted to lowercase
    - deduplicated while preserving order

    Uses a nested transaction/savepoint when creating a tag so that
    a unique-constraint race does not roll back the main recipe transaction.
    """

    # Normalize, clean, and deduplicate tag names
    seen = set()
    normalized = []

    for name in tag_names:
        clean = name.strip().lower()

        if clean and clean not in seen:
            seen.add(clean)
            normalized.append(clean)

    if not normalized:
        return []

    # Fetch existing tags in one query
    result = await session.execute(
        select(Tag).where(Tag.name.in_(normalized))
    )

    existing = {
        tag.name: tag.id
        for tag in result.scalars().all()
    }

    # Determine which tags don't exist yet
    missing = [
        name
        for name in normalized
        if name not in existing
    ]

    # Create missing tags
    for name in missing:
        try:
            # Savepoint:
            # If this INSERT fails, only this nested transaction is rolled back.
            async with session.begin_nested():
                tag = Tag(name=name)
                session.add(tag)

                # Flush so the database generates tag.id
                await session.flush()

            # Nested transaction succeeded
            existing[name] = tag.id

        except IntegrityError:
            # Another request may have created this tag concurrently.
            # The savepoint was rolled back, but the main transaction remains intact.

            result = await session.execute(
                select(Tag).where(Tag.name == name)
            )

            tag = result.scalars().first()

            if tag is None:
                # Something unexpected happened.
                raise

            existing[name] = tag.id

    # Return IDs in the same order as the normalized tag names
    return [
        existing[name]
        for name in normalized
    ]


async def create_recipe_service(
    request,
    current_user: dict,
):
    """
    Create a recipe and all related records.

    Creates:
    - Recipe
    - RecipeCategory
    - RecipeIngredient
    - RecipeInstruction
    - Tag
    - RecipeTag

    Everything is committed as one transaction.
    """

    # Remove nested/relationship data from Recipe model data
    recipe_data = request.model_dump(
        exclude={
            "ingredients",
            "instructions",
            "category_ids",
            "tag_names",
            "image_urls",
        }
    )

    # ---------------------------------------------------------
    # Normalize cooked weight to grams for consistent downstream
    # math (nutrition per serving, per-gram calculations, etc.)
    # ---------------------------------------------------------
    if request.cooked_weight_amount is not None:
        recipe_data["cooked_weight_grams"] = to_grams(
            request.cooked_weight_amount,
            request.cooked_weight_unit,
        )

    # cooked_weight_unit comes through model_dump() as the enum's
    # value (a plain string), which SQLAlchemy's Enum column accepts
    # directly, so no extra conversion is needed here.

    async with SessionLocal() as session:
        try:
            # ---------------------------------------------------------
            # 1. Create recipe
            # ---------------------------------------------------------

            recipe = Recipe(
                **recipe_data,
                user_id=current_user["id"],
            )

            session.add(recipe)

            # Flush so recipe.id becomes available
            await session.flush()

            # ---------------------------------------------------------
            # 2. Create recipe categories
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
            # 3. Create recipe ingredients
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
            # 4. Create recipe instructions
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
            # 5. Get/create tags
            # ---------------------------------------------------------

            tag_ids = await _get_or_create_tag_ids(
                session,
                request.tag_names,
            )

            # ---------------------------------------------------------
            # 6. Create recipe-tag relationships
            # ---------------------------------------------------------

            if tag_ids:
                session.add_all(
                    RecipeTag(
                        recipe_id=recipe.id,
                        tag_id=tag_id,
                    )
                    for tag_id in tag_ids
                )

            # ---------------------------------------------------------
            # 7. Image URLs
            # ---------------------------------------------------------
            #
            # image_urls is currently excluded from recipe_data.
            # Add image upload/storage logic here later.
            #

            # ---------------------------------------------------------
            # 8. Commit everything
            # ---------------------------------------------------------

            await session.commit()

            # Refresh recipe with database-generated values
            await session.refresh(recipe)

            return recipe

        except Exception:
            # Roll back the entire recipe transaction if anything
            # outside the tag savepoints fails.
            await session.rollback()
            raise