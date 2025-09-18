import asyncio
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates
import psycopg2
import psycopg2.extras  # ВАЖНО: импорт extras
from secret import Db
from .add_db_tables import (
    add_db_tables_collections_tb,
    add_db_tables_products_tb,
    add_db_tables_variants_tb,
    add_db_tables_user_cart_tb,
)

router = APIRouter()
templates = Jinja2Templates(directory="public")

def create_connection():
    return psycopg2.connect(
        host=Db.host,
        database=Db.database,
        user=Db.user,
        password=Db.password
    )

@router.get("/admin")
async def admin_endpoint(request: Request):
    insales_id = request.query_params.get("insales_id")
    shop = request.query_params.get("shop")
    if not insales_id or not shop:
        raise HTTPException(status_code=400, detail="insales_id and shop are required")

    try:
        conn = create_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(
            """
            INSERT INTO users_tb (insales_id, shop)
            VALUES (%s, %s)
            ON CONFLICT (insales_id, shop) DO NOTHING
            """,
            (insales_id, shop)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        # Логируем, но не роняем страницу
        print(f"/admin: users_tb insert warn: {e}")

    # 2) Пытаемся создать таблицы магазина, но не роняем страницу
    try:
        add_db_tables_collections_tb("shops_db", f"{shop}_{insales_id}")
        add_db_tables_products_tb("shops_db", f"{shop}_{insales_id}")
        add_db_tables_variants_tb("shops_db", f"{shop}_{insales_id}")
        add_db_tables_user_cart_tb("shops_db", f"{shop}_{insales_id}")
    except Exception as e:
        print(f"/admin: create shop tables warn: {e}")

    # 3) Всегда рендерим страницу; поля подтянет JS через /admin/settings/load
    return templates.TemplateResponse("admin.html", {"request": request})
