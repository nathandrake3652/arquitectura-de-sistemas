from fastapi import APIRouter

from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.ingredients import router as ingredients_router
from app.api.v1.endpoints.products import router as products_router
from app.api.v1.endpoints.recipe_items import router as recipe_items_router

api_router = APIRouter()
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(ingredients_router, prefix="/ingredients", tags=["catalog"])
api_router.include_router(products_router, prefix="/products", tags=["catalog"])
api_router.include_router(recipe_items_router, prefix="/recipe-items", tags=["catalog"])
