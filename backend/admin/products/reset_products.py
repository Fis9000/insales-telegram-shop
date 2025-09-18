# reset_products.py
from fastapi import APIRouter, HTTPException, Request
import aiohttp
import asyncpg
from datetime import datetime, timezone
from typing import List, Dict, Any

import psycopg2
from secret import Db

router = APIRouter()

def create_connection():
    return psycopg2.connect(
        host=Db.host,
        database=Db.database,
        user=Db.user,
        password=Db.password
    )

def safe_prefix(shop: str, insales_id: int) -> str:
    prefix = f"{shop}_{insales_id}"
    return prefix.replace('.', '_').replace('-', '_').replace(' ', '_')

def parse_dt_naive_utc(value: str):
    if not value:
        return None
    s = value.replace('Z', '+00:00')
    dt = datetime.fromisoformat(s)
    # Приводим к naive UTC, т.к. в таблицах TIMESTAMP без TZ.
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt

async def fetch_products_page(session: aiohttp.ClientSession, shop: str, auth: str, per_page: int, page: int):
    url = f"https://{shop}/admin/products.json?per_page={per_page}&page={page}"
    headers = {
        'Authorization': auth,                 # ВАЖНО: ключ — строка 'Authorization', значение — строка "Basic ... "
        'Accept': 'application/json',
        'User-Agent': 'Telegram-Shop-App/1.0',
    }
    async with session.get(url, headers=headers, timeout=60) as resp:
        if resp.status == 200:
            return await resp.json()
        elif resp.status == 404:
            raise HTTPException(status_code=404, detail="Товары не найдены")
        elif resp.status == 403:
            raise HTTPException(status_code=403, detail="Нет доступа к API магазина")
        else:
            text = await resp.text()
            raise HTTPException(status_code=resp.status, detail=f"Ошибка InSales: {text}")

async def fetch_all_products(shop: str, auth: str) -> List[Dict[str, Any]]:
    per_page = 250
    page = 1
    out: List[Dict[str, Any]] = []
    async with aiohttp.ClientSession() as session:
        while True:
            data = await fetch_products_page(session, shop, auth, per_page, page)
            if not data:
                break
            out.extend(data)
            page += 1
    return out

async def save_products_and_variants(shop: str, insales_id: int, products: List[Dict[str, Any]]):
    conn: asyncpg.Connection = await asyncpg.connect(
        host=Db.host,
        database="shops_db",
        user=Db.user,
        password=Db.password
    )
    try:
        sp = safe_prefix(shop, insales_id)
        products_table = f"shop_{sp}_products_tb"
        variants_table = f"shop_{sp}_variants_tb"

        prod_values = []
        var_values = []

        now_naive_utc = datetime.utcnow().replace(tzinfo=None)

        for p in products:
            updated_raw = p.get('updated_at') or p.get('created_at')
            updated_dt = parse_dt_naive_utc(updated_raw) or now_naive_utc

            # картинки (до 9, т.к. в вашей схеме image_0..image_8)
            images = [img.get('original_url') for img in (p.get('images') or [])][:9]
            images_dict = {}
            for i in range(9):
                images_dict[f"image_{i}"] = images[i] if i < len(images) else None

            # structure/material
            material_value = None
            for fv in (p.get('product_field_values') or []):
                if fv.get('product_field_id') == 88358:
                    material_value = fv.get('value')
                    break

            variants = p.get('variants') or []
            base_price = variants[0].get('base_price') if variants else None
            old_price = variants[0].get('old_price') if variants else None

            # соответствие вашей схеме shop_{..}_products_tb
            prod_values.append((
                p.get('id'),                         # product_id BIGINT PRIMARY KEY
                p.get('title'),                      # title
                p.get('description'),                # description
                images_dict.get('image_0'),
                images_dict.get('image_1'),
                images_dict.get('image_2'),
                base_price,                          # base_price NUMERIC
                old_price,                           # old_price NUMERIC
                material_value,                      # structure TEXT
                p.get('is_hidden'),                  # is_hidden BOOL
                updated_dt,                          # updated_date TIMESTAMP (naive UTC)
                # flags в вашей схеме: is_collection_new, is_collection_sale (если хотите — вычисляйте тут; пропустим -> NULL)
                None,                                # is_collection_new BOOL
                None,                                # is_collection_sale BOOL
                images_dict.get('image_3'),
                images_dict.get('image_4'),
                images_dict.get('image_5'),
                images_dict.get('image_6'),
                images_dict.get('image_7'),
                images_dict.get('image_8'),
                (p.get('collections_ids') or None),  # collection_ids BIGINT[]
                p.get('available'),                  # available BOOL
                p.get('canonical_url_collection_id') # canonical_url_collection_id TEXT
            ))

            # variants по вашей схеме: product_id, variant_id (PK), title, updated_date, variant_price
            for v in variants:
                var_values.append((
                    p.get('id'),
                    v.get('id'),
                    v.get('title'),
                    updated_dt,
                    v.get('price') or v.get('base_price')
                ))

        # Очистка и вставка
        await conn.execute(f"TRUNCATE {products_table} RESTART IDENTITY")
        insert_products_sql = f"""
            INSERT INTO {products_table} (
                product_id, title, description,
                image_0, image_1, image_2,
                base_price, old_price, structure,
                is_hidden, updated_date,
                is_collection_new, is_collection_sale,
                image_3, image_4, image_5, image_6, image_7, image_8,
                collection_ids, available, canonical_url_collection_id
            ) VALUES (
                $1,$2,$3,
                $4,$5,$6,
                $7,$8,$9,
                $10,$11,
                $12,$13,
                $14,$15,$16,$17,$18,$19,
                $20,$21,$22
            )
            ON CONFLICT (product_id) DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                image_0 = EXCLUDED.image_0,
                image_1 = EXCLUDED.image_1,
                image_2 = EXCLUDED.image_2,
                base_price = EXCLUDED.base_price,
                old_price = EXCLUDED.old_price,
                structure = EXCLUDED.structure,
                is_hidden = EXCLUDED.is_hidden,
                updated_date = EXCLUDED.updated_date,
                is_collection_new = EXCLUDED.is_collection_new,
                is_collection_sale = EXCLUDED.is_collection_sale,
                image_3 = EXCLUDED.image_3,
                image_4 = EXCLUDED.image_4,
                image_5 = EXCLUDED.image_5,
                image_6 = EXCLUDED.image_6,
                image_7 = EXCLUDED.image_7,
                image_8 = EXCLUDED.image_8,
                collection_ids = EXCLUDED.collection_ids,
                available = EXCLUDED.available,
                canonical_url_collection_id = EXCLUDED.canonical_url_collection_id
        """
        await conn.executemany(insert_products_sql, prod_values)

        await conn.execute(f"TRUNCATE {variants_table} RESTART IDENTITY")
        insert_variants_sql = f"""
            INSERT INTO {variants_table} (
                product_id, variant_id, title, updated_date, variant_price
            ) VALUES ($1,$2,$3,$4,$5)
            ON CONFLICT (variant_id) DO UPDATE SET
                product_id = EXCLUDED.product_id,
                title = EXCLUDED.title,
                updated_date = EXCLUDED.updated_date,
                variant_price = EXCLUDED.variant_price
        """
        if var_values:
            await conn.executemany(insert_variants_sql, var_values)

        return True
    finally:
        await conn.close()

@router.post("/reset_products")
async def reset_products(request: Request):
    """
    Синхронизация товаров: берём insales_id и shop из тела запроса,
    достаём inales_api_token из БД, тянем товары из InSales и сохраняем
    в таблицы конкретного магазина.
    """
    try:
        data = await request.json()
        insales_id_raw = data.get("insales_id")
        shop = (data.get("shop") or "").strip()
        if not insales_id_raw or not shop:
            raise HTTPException(status_code=400, detail="insales_id и shop обязательны")
        try:
            insales_id = int(insales_id_raw)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="insales_id должен быть числом")

        # Берём токен из БД по паре (insales_id, shop)
        conn = create_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT inales_api_token
            FROM users_tb
            WHERE insales_id = %s AND shop = %s
            LIMIT 1
            """,
            (insales_id, shop)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()

        if not row or not row[0] or not isinstance(row[0], str):
            raise HTTPException(status_code=404, detail="Токен не найден или некорректен")

        auth = row[0]  # строка "Basic ..."

        # Тянем товары (постранично)
        products = await fetch_all_products(shop, auth)
        if not products:
            return {"status": "success", "message": "Нет товаров для синхронизации", "count": 0}

        # Сохраняем
        ok = await save_products_and_variants(shop, insales_id, products)
        if not ok:
            raise HTTPException(status_code=500, detail="Ошибка сохранения товаров")

        return {"status": "success", "message": f"Синхронизировано {len(products)} товаров", "count": len(products)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка синхронизации товаров: {e}")
