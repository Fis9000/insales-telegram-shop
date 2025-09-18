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

@router.get("/show_collections")
def get_collections(request: Request):
    """Получение коллекций на основе Referer URL"""
    return get_collections_tb(request)

def get_collections_tb(request: Request):
    """Отображение коллекций конкретного магазина на основе URL"""    
    # Получаем URL откуда пришел запрос (Referer)
    referer = request.headers.get("referer") or ""
    
    # Если Referer пустой, попробуем взять из параметров запроса
    if not referer:
        # Альтернативный способ - прямая передача параметров
        insales_id = request.query_params.get("insales_id")
        shop = request.query_params.get("shop")
        
        if insales_id and shop:
            table_name = build_table_name(shop, insales_id)
        else:
            raise HTTPException(status_code=400, detail="Не удалось определить параметры магазина")
    else:
        # Извлекаем параметры из Referer URL
        insales_id, shop = extract_params_from_url(referer)
        if not insales_id or not shop:
            raise HTTPException(status_code=400, detail="Неверный формат URL")
        
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
        
        # Получаем коллекции из таблицы конкретного магазина
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

def extract_params_from_url(url: str):
    """Извлекает insales_id и shop_domain из URL"""
    # Паттерн для URL вида /main/{insales_id}/{shop_domain}
    pattern = r'/main/(\d+)/([^/?#]+)'
    match = re.search(pattern, url)
    
    if match:
        insales_id = match.group(1)
        shop_domain = match.group(2)
        return insales_id, shop_domain
    
    return None, None

def build_table_name(shop: str, insales_id: str):
    """Формирует имя таблицы коллекций для конкретного магазина"""
    prefix = f"{shop}_{insales_id}"
    safe_prefix = prefix.replace('.', '_').replace('-', '_').replace(' ', '_')
    return f"shop_{safe_prefix}_collections_tb"