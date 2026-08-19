from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from cooking_compass.core.db import SessionLocal
from cooking_compass.models.ingredients import Ingredient


async def create_ingredient_service(request):
    async with SessionLocal() as session:
        ingredient = Ingredient(**request.model_dump())

        session.add(ingredient)

        try:
            await session.commit()

        except IntegrityError as e:
            await session.rollback()

            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "message": f"Could not create ingredient: {str(e.orig)}",
                },
            )

        await session.refresh(ingredient)

        return ingredient