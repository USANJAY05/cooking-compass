from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from cooking_compass.core.db import SessionLocal
from cooking_compass.models.categories import Category


async def delete_category_service(
    category_id: int,
):
    async with SessionLocal() as session:
        category = await session.get(
            Category,
            category_id,
        )

        if not category:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "message": "Category not found",
                },
            )

        await session.delete(category)

        try:
            await session.commit()

        except IntegrityError:
            await session.rollback()

            raise HTTPException(
                status_code=409,
                detail={
                    "success": False,
                    "message": (
                        "Cannot delete category still "
                        "referenced by recipes"
                    ),
                },
            )

        return None