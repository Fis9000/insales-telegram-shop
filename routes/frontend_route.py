from fastapi import APIRouter

frontend_router = APIRouter()

# Стартовая страница
from tg_bot.start import router as start_router
frontend_router.include_router(start_router)

# Админка
from backend.admin.show_admin_panel import router as show_admin_panel
frontend_router.include_router(show_admin_panel)