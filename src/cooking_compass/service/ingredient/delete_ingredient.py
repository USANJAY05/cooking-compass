from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from cooking_compass.core.db import SessionLocal
from cooking_compass.models.ingredients import Ingredient


async def delete_ingredient_service(
    ingredient_id: int,
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

        await session.delete(ingredient)

        try:
            await session.commit()

        except IntegrityError:
            await session.rollback()

            raise HTTPException(
                status_code=409,
                detail={
                    "success": False,
                    "message": (
                        "Cannot delete ingredient still "
                        "referenced by recipes"
                    ),
                },
            )

        return None