from sqlalchemy import select

from cooking_compass.core.db import SessionLocal
from cooking_compass.models.ingredients import Ingredient


async def list_ingredients_service(
    page: int,
    page_size: int,
):
    async with SessionLocal() as session:

        offset = (page - 1) * page_size

        query = (
            select(Ingredient)
            .order_by(Ingredient.name)
            .offset(offset)
            .limit(page_size)
        )

        result = await session.execute(query)

        return result.scalars().all()