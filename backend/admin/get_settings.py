import base64
from fastapi import APIRouter, Request, HTTPException
import psycopg2
import psycopg2.extras
from secret import Db
from tg_bot.manager_instance import bot_manager

router = APIRouter()

def create_connection():
    return psycopg2.connect(
        host=Db.host,
        database=Db.database,
        user=Db.user,
        password=Db.password
    )

@router.post("/admin/settings/save")
async def save_settings(request: Request):
    """Сохраняем Идентификатор, Пароль и Токен в БД"""
    data = await request.json()

    insales_id_raw = data.get("insales_id")
    try:
        insales_id = int(insales_id_raw)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="insales_id должен быть числом")

    shop = (data.get("shop") or "").strip()
    identifier = data.get("identifier") or ""
    password = data.get("password") or ""
    token = (data.get("token") or "").strip()

    user_pass = f"{identifier}:{password}"
    api_token = base64.b64encode(user_pass.encode("utf-8")).decode("ascii")
    inales_api_token = f"Basic {api_token}"

    if not shop or not token:
        raise HTTPException(status_code=400, detail="Не все поля заполнены")

    try:
        conn = create_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO users_tb (insales_id, shop, identifier, password, token, is_active, inales_api_token)
            VALUES (%s, %s, %s, %s, %s, TRUE, %s)
            ON CONFLICT (insales_id, shop) DO UPDATE
            SET identifier = EXCLUDED.identifier,
                password   = EXCLUDED.password,
                token      = EXCLUDED.token,
                is_active  = TRUE,
                inales_api_token      = EXCLUDED.inales_api_token
            """,
            (insales_id, shop, identifier, password, token, inales_api_token)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[DB] save_settings error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка базы данных")

    # 5) Запуск/перезапуск бота
    ok = await bot_manager.start_bot(insales_id, shop, token, force_restart=True)
    if not ok:
        raise HTTPException(status_code=500, detail="Не удалось запустить бота (проверьте токен)")

    return {"status": "ok", "message": "Бот запущен!"}

@router.get("/admin/settings/load")
async def load_settings(insales_id: int, shop: str):
    """Получение сохранённых настроек из БД"""
    try:
        conn = create_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT identifier, password, token
            FROM users_tb
            WHERE insales_id = %s AND shop = %s
            LIMIT 1;
            """,
            (insales_id, shop)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            return {
                "status": "ok",
                "identifier": row[0],
                "password": row[1],
                "token": row[2]
            }
        else:
            return {"status": "empty"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@router.get("/admin/settings/load-last")
async def load_last_settings():
    """Получение последних сохраненных настроек"""
    try:
        print("Loading last settings from database...")
        conn = create_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT insales_id, shop 
            FROM users_tb 
            LIMIT 1
            """
        )
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        print(f"Database result: {result}")
        
        if result:
            return {
                "insales_id": result[0],
                "shop": result[1]
            }
        else:
            return {"insales_id": "", "shop": ""}
            
    except Exception as e:
        print(f"Error loading settings: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения настроек")