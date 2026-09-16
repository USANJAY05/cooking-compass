from fastapi import Depends, HTTPException
from cooking_compass.auth.keycloak import get_current_user
from cooking_compass.utils.check_user_exist import _resolve_user_id
from cooking_compass.utils.create_user import create_user


async def ensure_user_exists(current_user: dict = Depends(get_current_user)) -> dict:
    email = current_user.get("email")
    if not email:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": "User does not exist in context"},
        )

    try:
        user_id = await _resolve_user_id(email)
    except LookupError:
        user = await create_user(current_user)

        if user is None:
            try:
                user_id = await _resolve_user_id(email)
            except LookupError as exc:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "success": False,
                        "message": "Unable to create or resolve user",
                    },
                ) from exc
        else:
            user_id = user.id

    current_user["id"] = user_id
    return current_user
