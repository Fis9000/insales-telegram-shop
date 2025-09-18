from fastapi import APIRouter, Query, Request, HTTPException
from typing import List, Optional
import psycopg2
import psycopg2.extras
from secret import DbShops
import re

router = APIRouter()

PAGE_SIZE_DEFAULT = 12
PAGE_SIZE_MAX = 60

def create_connection():
    return psycopg2.connect(
        host=DbShops.host, 
        database=DbShops.database,
        user=DbShops.user, 
        password=DbShops.password
    )

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

def build_products_table_name(shop: str, insales_id: str):
    """Формирует имя таблицы продуктов для конкретного магазина"""
    prefix = f"{shop}_{insales_id}"
    safe_prefix = prefix.replace('.', '_').replace('-', '_').replace(' ', '_')
    return f"shop_{safe_prefix}_products_tb"

@router.get("/show_products")
def list_products(
    request: Request,
    limit: int = Query(PAGE_SIZE_DEFAULT, ge=1, le=PAGE_SIZE_MAX),
    offset: int = Query(0, ge=0),
    collection_id: Optional[int] = Query(None),
    q: Optional[str] = Query(None),
):
    """Получение списка продуктов для конкретного магазина"""
    
    # Получаем URL откуда пришел запрос (Referer)
    referer = request.headers.get("referer") or ""
    
    # Если Referer пустой, попробуем взять из параметров запроса
    if not referer:
        insales_id = request.query_params.get("insales_id")
        shop = request.query_params.get("shop")
        
        if insales_id and shop:
            table_name = build_products_table_name(shop, insales_id)
        else:
            raise HTTPException(status_code=400, detail="Не удалось определить параметры магазина")
    else:
        # Извлекаем параметры из Referer URL
        insales_id, shop = extract_params_from_url(referer)
        if not insales_id or not shop:
            raise HTTPException(status_code=400, detail="Неверный формат URL")
        
        table_name = build_products_table_name(shop, insales_id)
    
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
            raise HTTPException(status_code=404, detail=f"Таблица продуктов {table_name} не найдена")
        
        # Формируем базовый SQL запрос с динамическим именем таблицы
        sql = f"""
            SELECT product_id, title,
                   image_0, image_1, image_2, image_3, image_4,
                   image_5, image_6, image_7, image_8,
                   base_price, old_price
            FROM {table_name}
            WHERE is_hidden = FALSE
              AND available = TRUE
              AND canonical_url_collection_id IS NOT NULL
        """
        
        params: List = []
        
        # Добавляем фильтр по коллекции если указан
        if collection_id is not None:
            sql += " AND %s = ANY(collection_ids) "
            params.append(collection_id)
        
        # Добавляем поиск по названию если указан
        if q:
            sql += " AND title ILIKE %s "
            params.append(f"%{q}%")
        
        # Добавляем сортировку и пагинацию
        sql += " ORDER BY updated_date DESC, product_id DESC LIMIT %s OFFSET %s;"
        params.extend([limit, offset])

        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()

        def row_to_images(r) -> List[str]:
            """Собираем все изображения из полей image_0 ... image_8"""
            keys = [f"image_{i}" for i in range(9)]  # В вашей схеме image_0 до image_8
            urls = []
            for k in keys:
                v = r.get(k)
                if v:
                    s = str(v).strip()
                    if s:
                        urls.append(s)
            return urls

        # Формируем результат
        items = [{
            "product_id": r["product_id"],
            "title": r["title"],
            "images": row_to_images(r),
            "base_price": float(r["base_price"]) if r["base_price"] is not None else None,
            "old_price": float(r["old_price"]) if r["old_price"] is not None else None,
        } for r in rows]

        return {
            "items": items, 
            "limit": limit, 
            "offset": offset, 
            "has_more": len(items) == limit
        }
        
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Ошибка базы данных: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")
    finally:
        cursor.close()
        conn.close()
