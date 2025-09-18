from fastapi import APIRouter

admin_router = APIRouter()

# Админка
from backend.admin.show_admin_panel import router as show_admin_panel
admin_router.include_router(show_admin_panel)

# Сохранение настроек из админки
from backend.admin.get_settings import router as settings_router
admin_router.include_router(settings_router)
