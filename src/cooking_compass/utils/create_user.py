from sqlalchemy.exc import IntegrityError
from cooking_compass.core.db import SessionLocal
from cooking_compass.models.users import User


async def create_user(user_data: dict) -> User | None:
    async with SessionLocal() as session:
        user = User(
            keycloak_user_id=user_data.get("sub"),
            display_name=user_data.get("name") or user_data.get("preferred_username"),
            email=user_data.get("email"),
        )
        session.add(user)
        try:
            await session.commit()
        except IntegrityError:
            # Someone else created this user in a concurrent request — fine
            await session.rollback()
            return None
        await session.refresh(user)
        return user