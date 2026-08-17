from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from cooking_compass.core.db import SessionLocal
from cooking_compass.models.categories import Category


async def list_categories_service():
    async with SessionLocal() as session:
        result = await session.execute(select(Category))
        return result.scalars().all()


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
                detail={"success": False, "message": "Category already exists"},
            )
        await session.refresh(category)
        return category


async def update_category_service(category_id: int, request):
    async with SessionLocal() as session:
        category = await session.get(Category, category_id)
        if not category:
            raise HTTPException(status_code=404, detail={"success": False, "message": "Category not found"})

        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)

        await session.commit()
        await session.refresh(category)
        return category


async def delete_category_service(category_id: int):
    async with SessionLocal() as session:
        category = await session.get(Category, category_id)
        if not category:
            raise HTTPException(status_code=404, detail={"success": False, "message": "Category not found"})

        await session.delete(category)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=409,
                detail={"success": False, "message": "Cannot delete category still referenced by recipes"},
            )
        return None