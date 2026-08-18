from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from cooking_compass.core.db import SessionLocal
from cooking_compass.models.categories import Category


async def create_category_service(request):
    async with SessionLocal() as session:
        category = Category(**request.model_dump())

        session.add(category)

        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=409,
                detail={
                    "success": False,
                    "message": "Category already exists",
                },
            )

        await session.refresh(category)

        return category