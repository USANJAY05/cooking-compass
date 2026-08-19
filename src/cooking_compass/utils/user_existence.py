from cooking_compass.core.db import SessionLocal
from cooking_compass.models.users import User
from sqlalchemy import select

async def user_existence(email: str) -> bool:
    """
    Check if a user with the given email exists in the database asynchronously.
    Returns True if found, False otherwise.
    """
    try:
        async with SessionLocal() as session:
            result = await session.execute(select(User).filter_by(email=email))
            user = result.scalars().first()
            return user is not None
    except Exception as e:
        raise RuntimeError(f"Database error while checking user existence: {e}")