from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="public")

# Стартовая страница
# https://insales-tg-shop.ru/main = http://127.0.0.1:8080/main

@router.get("/main")
async def read_root(request: Request):
    return templates.TemplateResponse(
        "main.html",
        {"request": request}
    )
