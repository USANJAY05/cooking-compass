from datetime import date

from fastapi import APIRouter, Depends, status

from cooking_compass.auth.keycloak import get_current_user

from cooking_compass.schema.cart.request_schema import (
    GenerateCartRequest,
    UpdateCartItemRequest,
)

from cooking_compass.schema.cart.response_schema import (
    CartResponse,
    GenerateCartResponse,
    UpdateCartItemResponse,
)


router = APIRouter(
    prefix="/cart",
    tags=["CART"],
)


# ---------------------------------------------------------
# GET /cart
# Get current shopping cart
# ---------------------------------------------------------
@router.get(
    "/",
    response_model=CartResponse,
)
def get_cart(
    from_date: date | None = None,
    to_date: date | None = None,
    current_user: dict = Depends(get_current_user),
):
    return "get cart"


# ---------------------------------------------------------
# POST /cart/generate
# Generate cart from routines
# ---------------------------------------------------------
@router.post(
    "/generate",
    response_model=GenerateCartResponse,
    status_code=status.HTTP_200_OK,
)
def generate_cart(
    request: GenerateCartRequest,
    current_user: dict = Depends(get_current_user),
):
    return "generate cart"


# ---------------------------------------------------------
# PUT /cart/items/{ingredient_id}
# Update cart item
# ---------------------------------------------------------
@router.put(
    "/items/{ingredient_id}",
    response_model=UpdateCartItemResponse,
)
def update_cart_item(
    ingredient_id: int,
    request: UpdateCartItemRequest,
    current_user: dict = Depends(get_current_user),
):
    return "update cart item"


# ---------------------------------------------------------
# DELETE /cart/items/{ingredient_id}
# Remove item from cart
# ---------------------------------------------------------
@router.delete(
    "/items/{ingredient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_cart_item(
    ingredient_id: int,
    current_user: dict = Depends(get_current_user),
):
    return None


# ---------------------------------------------------------
# DELETE /cart
# Clear entire cart
# ---------------------------------------------------------
@router.delete(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
)
def clear_cart(
    current_user: dict = Depends(get_current_user),
):
    return None