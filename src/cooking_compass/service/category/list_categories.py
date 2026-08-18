from sqlalchemy import select

from cooking_compass.core.db import SessionLocal
from cooking_compass.models.categories import Category


async def list_categories_service(page: int, page_size: int):
    async with SessionLocal() as session:
        offset = (page - 1) * page_size

        result = await session.execute(
            select(Category)
            .offset(offset)
            .limit(page_size)
        )

        categories = result.scalars().all()

        return categories