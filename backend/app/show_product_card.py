from fastapi import APIRouter, HTTPException, Request, Path
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from secret import DbShops
import psycopg2
import psycopg2.extras
import re
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="public")

def create_connection():
    return psycopg2.connect(
        host=DbShops.host,
        database=DbShops.database,
        user=DbShops.user,
        password=DbShops.password
    )

def extract_params_from_url(url: str):
    """Извлекает insales_id и shop_domain из URL"""
    logger.info(f"[DEBUG] Extracting params from URL: {url}")
    
    # Паттерн для URL вида /main/{insales_id}/{shop_domain}
    pattern = r'/main/(\d+)/([^/?#]+)'
    match = re.search(pattern, url)
    
    if match:
        insales_id = match.group(1)
        shop_domain = match.group(2)
        logger.info(f"[DEBUG] Extracted: insales_id={insales_id}, shop_domain={shop_domain}")
        return insales_id, shop_domain
    
    logger.warning(f"[DEBUG] No match found for pattern in URL: {url}")
    return None, None

def build_table_names(shop: str, insales_id: str):
    """Формирует имена таблиц для конкретного магазина"""
    prefix = f"{shop}_{insales_id}"
    safe_prefix = prefix.replace('.', '_').replace('-', '_').replace(' ', '_')
    table_names = {
        'products': f"shop_{safe_prefix}_products_tb",
        'variants': f"shop_{safe_prefix}_variants_tb"
    }
    logger.info(f"[DEBUG] Built table names: {table_names}")
    return table_names

LETTER_ORDER = {
    'XXS': 1, 'XS': 2, 'S': 3, 'M': 4, 'L': 5, 'XL': 6,
    '2XL': 7, 'XXL': 7, '3XL': 8, 'XXXL': 8, '4XL': 9, 'XXXXL': 9,
}

def normalize_key(title: str) -> str:
    return ''.join(title.upper().split())

def size_sort_key(v):
    t = normalize_key(v['title'])
    if t in LETTER_ORDER:
        return (0, LETTER_ORDER[t], 0)
    if t.isdigit():
        return (1, int(t), 0)
    return (2, 0, t)

@router.get("/product/{product_id}", response_class=HTMLResponse)
def product_page(request: Request, product_id: int = Path(...)):
    """Страница товара с определением магазина по Referer"""
    
    logger.info(f"[DEBUG] product_page called: product_id={product_id}")
    logger.info(f"[DEBUG] Request headers: {dict(request.headers)}")
    
    # Получаем URL откуда пришел запрос (Referer)
    referer = request.headers.get("referer") or ""
    logger.info(f"[DEBUG] Referer: '{referer}'")
    
    # Проверяем query параметры (если переданы напрямую)
    query_insales_id = request.query_params.get("insales_id")
    query_shop = request.query_params.get("shop")
    
    if query_insales_id and query_shop:
        logger.info(f"[DEBUG] Using query params: insales_id={query_insales_id}, shop={query_shop}")
        insales_id, shop = query_insales_id, query_shop
        table_names = build_table_names(shop, insales_id)
    elif referer:
        # Извлекаем параметры из Referer URL
        insales_id, shop = extract_params_from_url(referer)
        if not insales_id or not shop:
            logger.error(f"[DEBUG] Failed to extract params from referer: {referer}")
            raise HTTPException(status_code=400, detail=f"Неверный формат URL в Referer: {referer}")
        
        table_names = build_table_names(shop, insales_id)
    else:
        # Если нет ни referer, ни параметров, используем последние настройки
        logger.info("[DEBUG] No referer or params, trying fallback")
        try:
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT insales_id, shop
                FROM users_tb
                ORDER BY created_at DESC
                LIMIT 1
            """)
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                insales_id, shop = result
                table_names = build_table_names(shop, str(insales_id))
                logger.info(f"[DEBUG] Using fallback: insales_id={insales_id}, shop={shop}")
            else:
                logger.error("[DEBUG] No fallback settings found")
                raise HTTPException(status_code=404, detail="Настройки магазина не найдены")
        except Exception as e:
            logger.error(f"[DEBUG] Fallback failed: {e}")
            raise HTTPException(status_code=404, detail="Не удалось определить магазин")
    
    # Получаем товар и варианты для конкретного магазина
    product = get_product_by_id(product_id, table_names['products'])
    if not product:
        logger.error(f"[DEBUG] Product {product_id} not found in {table_names['products']}")
        raise HTTPException(status_code=404, detail="Товар не найден")

    variants = get_variants_by_product_id(product_id, table_names['variants'])
    variants = sorted(variants, key=size_sort_key)
    
    logger.info(f"[DEBUG] Product found: {product['title']}, variants: {len(variants)}")

    return templates.TemplateResponse(
        "product.html", 
        {
            "request": request, 
            "product": product, 
            "variants": variants,
            "shop": shop,
            "insales_id": insales_id
        }
    )

def get_product_by_id(product_id: int, products_table: str):
    """Получить товар по ID из таблицы конкретного магазина"""
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        logger.info(f"[DEBUG] Checking if table exists: {products_table}")
        # Проверяем существование таблицы
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            );
        """, (products_table,))
        
        table_exists = cursor.fetchone()[0]
        logger.info(f"[DEBUG] Table {products_table} exists: {table_exists}")
        
        if not table_exists:
            logger.warning(f"[DEBUG] Table {products_table} not found")
            return None
        
        # Получаем товар из таблицы конкретного магазина
        logger.info(f"[DEBUG] Executing query on {products_table} for product_id {product_id}")
        cursor.execute(f"""
            SELECT
                product_id,
                title,
                description,
                image_0, image_1, image_2, image_3, image_4,
                image_5, image_6, image_7, image_8,
                base_price,
                old_price,
                structure,
                is_hidden,
                updated_date
            FROM {products_table}
            WHERE product_id = %s 
              AND is_hidden = FALSE 
              AND available = TRUE 
              AND canonical_url_collection_id IS NOT NULL;
        """, (product_id,))
        
        r = cursor.fetchone()
        if not r:
            logger.warning(f"[DEBUG] Product {product_id} not found in {products_table}")
            return None

        logger.info(f"[DEBUG] Product found: {r['title']}")

        # Собираем изображения
        images = [r[f"image_{i}"] for i in range(9)]  # image_0 до image_8
        images = [img for img in images if img and str(img).strip() and img != 'null']
        logger.info(f"[DEBUG] Product has {len(images)} images")

        return {
            "product_id": r["product_id"],
            "title": r["title"],
            "description": r["description"],
            "images": images,
            "base_price": float(r["base_price"]) if r["base_price"] else None,
            "old_price": float(r["old_price"]) if r["old_price"] else None,
            "structure": r["structure"],
            "updated_date": r["updated_date"]
        }
        
    except Exception as e:
        logger.error(f"[DEBUG] Error getting product: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_variants_by_product_id(product_id: int, variants_table: str):
    """Получить варианты товара из таблицы конкретного магазина"""
    conn = create_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        logger.info(f"[DEBUG] Checking variants table: {variants_table}")
        # Проверяем существование таблицы
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            );
        """, (variants_table,))
        
        table_exists = cursor.fetchone()[0]
        logger.info(f"[DEBUG] Variants table {variants_table} exists: {table_exists}")
        
        if not table_exists:
            logger.warning(f"[DEBUG] Variants table {variants_table} not found")
            return []
        
        # ОБНОВЛЕННЫЙ SQL с добавлением quantity
        cursor.execute(f"""
            SELECT
                variant_id,
                title,
                quantity,
                updated_date,
                variant_price
            FROM {variants_table}
            WHERE product_id = %s
            ORDER BY title;
        """, (product_id,))
        
        rows = cursor.fetchall()
        logger.info(f"[DEBUG] Found {len(rows)} variants")
        
        if not rows:
            return []

        variants = []
        for r in rows:
            variants.append({
                "variant_id": r["variant_id"],
                "title": r["title"],
                "quantity": r["quantity"] or 0,  # Используем реальное количество из БД
                "updated_date": r["updated_date"],
                "variant_price": r["variant_price"]
            })
        return variants
        
    except Exception as e:
        logger.error(f"[DEBUG] Error getting variants: {e}")
        return []
    finally:
        cursor.close()
        conn.close()
