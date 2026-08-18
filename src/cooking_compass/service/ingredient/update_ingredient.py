from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from cooking_compass.core.db import SessionLocal
from cooking_compass.models.ingredients import Ingredient


async def update_ingredient_service(
    ingredient_id: int,
    request,
):
    async with SessionLocal() as session:
        ingredient = await session.get(
            Ingredient,
            ingredient_id,
        )

        if not ingredient:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "message": "Ingredient not found",
                },
            )

        update_data = request.model_dump(
            exclude_unset=True
        )

        for field, value in update_data.items():
            setattr(ingredient, field, value)

        try:
            await session.commit()

        except IntegrityError as e:
            await session.rollback()

            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "message": (
                        f"Could not update ingredient: "
                        f"{str(e.orig)}"
                    ),
                },
            )

        await session.refresh(ingredient)

        return ingredient