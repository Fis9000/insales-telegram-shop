from fastapi import APIRouter

frontend_router = APIRouter()

# Стартовая страница
from tg_bot.start import router as start_router
frontend_router.include_router(start_router)
