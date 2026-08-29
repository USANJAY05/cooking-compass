from fastapi import APIRouter, Depends, Query

from sqlalchemy.ext.asyncio import AsyncSession

from cooking_compass.core.db import get_db

from cooking_compass.utils.ensure_user import ensure_user_exists
from cooking_compass.utils.check_user_exist import user_exist

from cooking_compass.schema.cart.response_schema import CartResponse

from cooking_compass.service.cart.get_cart import (
    get_cart_service,
)


router = APIRouter(
    prefix="/cart",
    tags=["CART"],
)


# =========================================================
# GET /cart
# Get shopping cart generated from user's routines
# =========================================================
@router.get(
    "/",
    response_model=CartResponse,
)
@user_exist
async def get_cart(
    days: int = Query(
        default=7,
        ge=1,
        le=30,
        description="Number of days to generate the shopping cart for",
    ),
    current_user: dict = Depends(ensure_user_exists),
    db: AsyncSession = Depends(get_db),
):
    return await get_cart_service(
        days=days,
        current_user=current_user,
        db=db,
    )