import re
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import psycopg2
from secret import DbShops

router = APIRouter()

def create_connection():
    return psycopg2.connect(
        host = DbShops.host,
        database = DbShops.database,
        user = DbShops.user,
        password = DbShops.password
    )

@router.get("/show_collections_admin")
def get_collections_admin(insales_id: str, shop: str):
    """Получение коллекций для админ панели по параметрам (только видимые)"""
    
    table_name = build_table_name(shop, insales_id)
    
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Проверяем существование таблицы
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            );
        """, (table_name,))
        
        if not cursor.fetchone()[0]:
            raise HTTPException(status_code=404, detail=f"Таблица коллекций {table_name} не найдена")
        
        # Получаем только видимые коллекции (is_hidden = false)
        cursor.execute(f"""
            SELECT id, title, position
            FROM {table_name}
            WHERE is_hidden = false
            ORDER BY position ASC;
        """)
        
        rows = cursor.fetchall()
        collections = [
            {
                "id": row["id"],
                "title": row["title"],
                "position": row["position"]
            }
            for row in rows
        ]
        
        return JSONResponse(content=collections)
        
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Ошибка базы данных: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def build_table_name(shop: str, insales_id: str):
    """Формирует имя таблицы коллекций для конкретного магазина"""
    prefix = f"{shop}_{insales_id}"
    safe_prefix = prefix.replace('.', '_').replace('-', '_').replace(' ', '_')
    return f"shop_{safe_prefix}_collections_tb"
