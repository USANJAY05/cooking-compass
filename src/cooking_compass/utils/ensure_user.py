from fastapi import Depends, HTTPException
from cooking_compass.auth.keycloak import get_current_user
from cooking_compass.utils.user_existence import user_existence
from cooking_compass.utils.create_user import create_user


async def ensure_user_exists(current_user: dict = Depends(get_current_user)) -> dict:
    print(current_user)
    email = current_user.get("email")
    if not email:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": "User does not exist in context"},
        )

    if not await user_existence(email):
        await create_user(current_user)

    return current_user