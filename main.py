# uvicorn main:app --reload
# uvicorn main:app --reload --port 8080
import asyncio
import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from routes import (frontend_router)

app = FastAPI()

if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.mount("/css", StaticFiles(directory="public/css"), name="css")
if os.path.isdir("public/js"):
    app.mount("/js", StaticFiles(directory="public/js"), name="js")

# Не индексировать в поисковиках
@app.middleware("http")
async def add_noindex_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response

# Разрешённые источники
ALLOWED_ORIGINS = [
    "http://127.0.0.1:8080",
    "http://localhost:8080",
    # при необходимости добавить продовый фронтенд, если он с другого origin
    # "https://shop.4forms-tech.ru",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],          # можно сузить под ваши заголовки
    allow_credentials=False,      # включайте True только если реально нужны cookie/Authorization
    expose_headers=["Content-Type"],
    max_age=86400,                # кэш preflight на сутки
)

templates = Jinja2Templates(directory="public")

app.include_router(frontend_router)

# ТГ бот
# from tg_bot.tg_bot import tg_shop_start_bot
# @app.on_event("startup")
# async def start_tg_shop_start_bot():
#     asyncio.create_task(tg_shop_start_bot())
#     print("Telegram bot | tg_shop | is running...")

@app.get("/") # https:// = http://127.0.0.1:8080/
def read_root():
    return {"message": "insales-telegram-shop"}

@app.get("/view_deploy_results", response_class=PlainTextResponse) # https:// = http://127.0.0.1:8080/view_deploy_results
async def read_logs():
    """Логи"""
    log_path = Path("view_deploy_results.txt")
    if log_path.exists():
        content = log_path.read_text(encoding="utf-8")
        return PlainTextResponse(content)
    else:
        return PlainTextResponse("Файл не найден", status_code=404)