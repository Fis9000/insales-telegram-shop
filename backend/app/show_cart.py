from typing import Dict, List
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from .cart_db import get_user_cart_db, bulk_update_cart_quantities, add_to_user_cart_db, delete_from_user_cart_db
from secret import Db, DbShops
import re
import psycopg2
from globals import get_logger

logger = get_logger("show_cart", "errors.log", logs_dir="logs")
router = APIRouter()
templates = Jinja2Templates(directory="public")

def extract_shop_params_from_referer(referer: str):
    """Извлекает параметры магазина из Referer URL"""
    if not referer:
        return None, None
    
    # Паттерн для URL вида /main/{insales_id}/{shop_domain}
    pattern = r'/main/(\d+)/([^/?#]+)'
    match = re.search(pattern, referer)
    
    if match:
        insales_id = match[1]
        shop_domain = match[2]
        return insales_id, shop_domain
    
    return None, None

def get_fallback_shop_params():
    """Получает параметры магазина из users_db как fallback"""
    try:
        conn = psycopg2.connect(
            host=Db.host,
            database=Db.database,
            user=Db.user,
            password=Db.password
        )
        cursor = conn.cursor()
        cursor.execute("SELECT insales_id, shop FROM users_tb LIMIT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return str(result[0]), result[1]
    except Exception as e:
        logger.error(f"Fallback failed: {e}")
    
    return None, None

@router.get("/cart", response_class=HTMLResponse)
async def cart_page(request: Request):
    return templates.TemplateResponse("cart.html", {"request": request})

@router.post("/cart")
async def get_cart(request: Request):
    """Корзина клиента для конкретного магазина"""
    data = await request.json()
    user_id = data.get("user_id")
    shop = data.get("shop")
    insales_id = data.get("insales_id")
    
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id не передан")
    
    # Если параметры переданы в body, используем их
    if shop and insales_id:
        return get_user_cart_db(user_id, shop, insales_id)
    
    # Иначе пробуем определить из Referer (как раньше)
    referer = request.headers.get("referer", "")
    insales_id, shop = extract_shop_params_from_referer(referer)
    
    if not insales_id or not shop:
        insales_id, shop = get_fallback_shop_params()
        if not insales_id or not shop:
            raise HTTPException(status_code=400, detail="Не удалось определить магазин")
    
    return get_user_cart_db(user_id, shop, insales_id)

@router.post("/cart/update_quantities")
async def update_quantities(request: Request):
    """Обновление количества товаров в корзине"""
    payload = await request.json()
    user_id = payload.get("user_id")
    items: List[Dict] = payload.get("items", [])
    
    if not user_id or not isinstance(items, list) or len(items) == 0:
        return JSONResponse({"status": "error", "message": "invalid payload"}, status_code=400)
    
    # Определяем магазин
    referer = request.headers.get("referer", "")
    insales_id, shop = extract_shop_params_from_referer(referer)
    
    if not insales_id or not shop:
        insales_id, shop = get_fallback_shop_params()
        if not insales_id or not shop:
            return JSONResponse({"status": "error", "message": "Не удалось определить магазин"}, status_code=400)
    
    # Нормализация количеств
    norm_items = []
    for it in items:
        try:
            vid = int(it.get("variant_id"))
            qty = int(it.get("quantity", 1))
            if qty < 1:
                qty = 1
            norm_items.append({"variant_id": vid, "quantity": qty})
        except Exception:
            continue
    
    if not norm_items:
        return JSONResponse({"status": "error", "message": "no valid items"}, status_code=400)
    
    try:
        bulk_update_cart_quantities(str(user_id), norm_items, shop, insales_id)
        return JSONResponse({"status": "success"})
    except Exception as e:
        logger.error(f"Не удалось обновить корзину: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@router.post('/add_to_cart')
async def add_to_cart(request: Request):
    """Добавление товара в корзину"""
    data = await request.json()
    
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    variant_id = data.get('variant_id')
    variant_price = data.get('variant_price')
    image_0 = data.get('image_0')
    variant_title = data.get('variant_title')
    product_title = data.get('product_title')
    shop = data.get('shop')
    insales_id = data.get('insales_id')
    
    if not user_id or not product_id or not variant_id or not shop or not insales_id:
        raise HTTPException(status_code=400, detail='Отсутствуют обязательные параметры')
    
    try:
        add_to_user_cart_db(
            user_id=user_id, 
            product_id=product_id, 
            variant_id=variant_id, 
            variant_price=variant_price, 
            image_0=image_0, 
            variant_title=variant_title, 
            product_title=product_title,
            shop=shop,
            insales_id=insales_id
        )
        return JSONResponse(content={'status': 'success'})
    except Exception as e:
        logger.error(f"Ошибка добавления в корзину: {e}")
        raise HTTPException(status_code=500, detail=f'Database error: {e}')

@router.post("/cart/delete")
async def delete_from_cart(request: Request):
    """Удаление товара из корзины"""
    data = await request.json()
    user_id = data.get("user_id")
    variant_id = data.get("variant_id")
    
    if not user_id or not variant_id:
        raise HTTPException(status_code=400, detail="Отсутствуют параметры")
    
    # Определяем магазин
    referer = request.headers.get("referer", "")
    insales_id, shop = extract_shop_params_from_referer(referer)
    
    if not insales_id or not shop:
        insales_id, shop = get_fallback_shop_params()
        if not insales_id or not shop:
            raise HTTPException(status_code=400, detail="Не удалось определить магазин")
    
    try:
        delete_from_user_cart_db(user_id, variant_id, shop, insales_id)
        return JSONResponse({"status": "success"})
    except Exception as e:
        logger.error(f"Ошибка удаления из корзины: {e}")
        raise HTTPException(status_code=500, detail=str(e))
