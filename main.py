# uvicorn main:app --reload
# uvicorn main:app --reload --port 8006
import asyncio
import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

@app.get("/") # https://4forms-tech.ru/chats_service = 127.0.0.1:8080
def read_root():
    return {"message": "insales-telegram-shop"}

@app.get("/view_deploy_results", response_class=PlainTextResponse) # https://4forms-tech.ru/chats_service/view_deploy_results = 127.0.0.1:8080/view_deploy_results
async def read_logs():
    """Логи"""
    log_path = Path("view_deploy_results.txt")
    if log_path.exists():
        content = log_path.read_text(encoding="utf-8")
        return PlainTextResponse(content)
    else:
        return PlainTextResponse("Файл не найден", status_code=404)