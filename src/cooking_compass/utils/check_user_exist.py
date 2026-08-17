from functools import wraps
import inspect
from fastapi import HTTPException
from sqlalchemy import select

from cooking_compass.core.db import SessionLocal
from cooking_compass.models.users import User
from .create_user import create_user


def user_exist(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        current_user = kwargs.get("current_user")

        if not current_user or not current_user.get("email"):
            raise HTTPException(
                status_code=400,
                detail={"success": False, "message": "User does not exist in context"},
            )

        email = current_user.get("email")

        async with SessionLocal() as session:
            result = await session.execute(select(User).filter_by(email=email))
            user = result.scalars().first()

            if not user:
                user = await create_user(current_user)
                if user is None:
                    result = await session.execute(select(User).filter_by(email=email))
                    user = result.scalars().first()

        current_user["id"] = user.id   # ← the missing piece
        kwargs["current_user"] = current_user

        if inspect.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        return func(*args, **kwargs)

    return wrapper