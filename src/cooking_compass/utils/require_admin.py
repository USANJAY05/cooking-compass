from fastapi import Depends, HTTPException

from cooking_compass.utils.ensure_user import ensure_user_exists


async def require_admin(current_user: dict = Depends(ensure_user_exists)) -> dict:
    print("CURRENT USER:")
    print(current_user)

    roles = current_user.get("realm_access", {}).get("roles", [])

    print("ROLES:", roles)

    if "admin" not in roles:
        raise HTTPException(
            status_code=403,
            detail={"success": False, "message": "Admin access required"},
        )

    return current_user