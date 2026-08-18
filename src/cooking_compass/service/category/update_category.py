from fastapi import HTTPException

from cooking_compass.core.db import SessionLocal
from cooking_compass.models.categories import Category


async def update_category_service(
    category_id: int,
    request,
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

        update_data = request.model_dump(
            exclude_unset=True
        )

        for field, value in update_data.items():
            setattr(category, field, value)

        await session.commit()
        await session.refresh(category)

        return category