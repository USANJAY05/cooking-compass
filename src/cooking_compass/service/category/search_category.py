from sqlalchemy import select

from cooking_compass.core.db import SessionLocal
from cooking_compass.models.categories import Category


async def search_categories_service(
    q: str,
    page: int,
    page_size: int,
):
    async with SessionLocal() as session:

        offset = (page - 1) * page_size

        search_text = q.strip().lower()

        query = (
            select(Category)
            .where(
                Category.name.ilike(f"{search_text}%")
            )
            .order_by(Category.name)
            .offset(offset)
            .limit(page_size)
        )

        result = await session.execute(query)

        return result.scalars().all()