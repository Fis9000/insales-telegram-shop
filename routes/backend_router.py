from fastapi import APIRouter

backend_router = APIRouter()

# Коллекции ресет
from backend.admin.collections.reset_collections import router as reset_collections_router
backend_router.include_router(reset_collections_router)

# Товары ресет
from backend.admin.products.reset_products import router as reset_products_router
backend_router.include_router(reset_products_router)

# Коллекции отображение
from backend.app.show_collections import router as show_collections_router
backend_router.include_router(show_collections_router)

# Коллекции отображение в админке
from backend.admin.collections.show_collections_admin import router as show_collections_admin_router
backend_router.include_router(show_collections_admin_router)

# Товары отображение
from backend.app.show_products import router as show_products_router
backend_router.include_router(show_products_router)