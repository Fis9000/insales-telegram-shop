import aiohttp
import asyncpg
from fastapi import HTTPException
import psycopg2
from secret import Db
from datetime import datetime, timezone

def create_connection():
    return psycopg2.connect(
        host=Db.host,
        database=Db.database,
        user=Db.user,
        password=Db.password
    )

async def fetch_collections_from_insales(shop: str, inales_api_token: str):
    """Получение коллекций из InSales API"""
    try:
        url = f"https://{shop}/admin/collections.json"
        async with aiohttp.ClientSession() as session:
            headers = {
                'Authorization': inales_api_token,  # "Basic base64(id:pass)"
                'Content-Type': 'application/json',
                'User-Agent': 'Telegram-Shop-App/1.0',
            }
            async with session.get(url, headers=headers, timeout=30) as response:
                if response.status == 200:
                    collections_data = await response.json()
                    filtered = [
                        c for c in collections_data
                        if c.get("title") != "Каталог"
                    ]
                    return filtered
                else:
                    error_text = await response.text()
                    raise HTTPException(status_code=response.status, detail=f"InSales API error {response.status}: {error_text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения коллекций: {str(e)}")

async def save_collections_to_shop_db(shop: str, insales_id: int, collections_data: list):
    """Сохранение коллекций в таблицу конкретного магазина в общей БД"""
    conn = None
    try:
        conn = await asyncpg.connect(
            host=Db.host,
            database="shops_db",  # общая БД с таблицами магазинов
            user=Db.user,
            password=Db.password
        )
        prefix = f"{shop}_{insales_id}"
        safe_prefix = prefix.replace('.', '_').replace('-', '_').replace(' ', '_')
        table_name = f"shop_{safe_prefix}_collections_tb"

        await conn.execute(f'DELETE FROM {table_name}')

        insert_sql = f"""
            INSERT INTO {table_name}
            (id, title, position, is_hidden, updated_at, parent_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (id) DO UPDATE
            SET title = EXCLUDED.title,
                position = EXCLUDED.position,
                is_hidden = EXCLUDED.is_hidden,
                updated_at = EXCLUDED.updated_at,
                parent_id = EXCLUDED.parent_id
        """
        
        def parse_dt_naive_utc(value: str):
            if not value:
                return None
            # Пример входа: '2025-06-26T13:24:15.000+03:00' или '...Z'
            s = value.replace('Z', '+00:00')
            dt = datetime.fromisoformat(s)  # dt может быть aware или naive
            if dt.tzinfo is not None:
                # Переводим к UTC и убираем tzinfo
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            # Если был naive — оставляем как есть (наивный UTC)
            return dt

        values = []
        for c in collections_data:
            updated_raw = c.get("updated_at") or c.get("created_at")
            updated_dt = parse_dt_naive_utc(updated_raw)
            values.append((
                c.get("id"),
                c.get("title", ""),
                c.get("position", 0),
                c.get("is_hidden", False),
                updated_dt,  # naive UTC datetime
                c.get("parent_id"),
            ))
        await conn.executemany(insert_sql, values)
        return True
    except Exception as e:
        print(f"Ошибка сохранения коллекций в БД: {e}")
        return False
    finally:
        if conn:
            await conn.close()
