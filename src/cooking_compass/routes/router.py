from fastapi import APIRouter
from cooking_compass.routes.cart import router as cart_router
from cooking_compass.routes.recipe import router as recipe_router
from cooking_compass.routes.routine import router as routine_router
from cooking_compass.routes.category import router as category_router
from cooking_compass.routes.ingredient import router as ingredient_router

router = APIRouter(
    prefix="/api/v1"
)

router.include_router(cart_router)
router.include_router(recipe_router)
router.include_router(routine_router)
router.include_router(category_router)
router.include_router(ingredient_router)
