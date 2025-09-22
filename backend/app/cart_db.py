from typing import Dict, List
import psycopg2
import psycopg2.extras
from secret import Db, DbShops

def create_users_connection():
    return psycopg2.connect(
        host=Db.host,
        database=Db.database,
        user=Db.user,
        password=Db.password
    )

def create_shops_connection():
    return psycopg2.connect(
        host=DbShops.host,
        database=DbShops.database,
        user=DbShops.user,
        password=DbShops.password
    )

def build_cart_table_name(shop: str, insales_id: str):
    """Формирует имя таблицы корзины для конкретного магазина"""
    prefix = f"{shop}_{insales_id}"
    safe_prefix = prefix.replace('.', '_').replace('-', '_').replace(' ', '_')
    return f"shop_{safe_prefix}_user_cart_tb"

def ensure_cart_table_exists(shop: str, insales_id: str):
    """Создает таблицу корзины если её нет"""
    table_name = build_cart_table_name(shop, insales_id)
    conn = create_shops_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                product_id INTEGER NOT NULL,
                variant_id INTEGER NOT NULL,
                variant_price DECIMAL(10, 2),
                image_0 TEXT,
                variant_title VARCHAR(255),
                product_title VARCHAR(255),
                quantity INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, variant_id)
            );
        """)
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def add_to_user_cart_db(user_id: str, product_id: int, variant_id: int, variant_price: float,
                       image_0: str, variant_title: str, product_title: str, shop: str, insales_id: str):
    """Добавить товар в корзину конкретного магазина"""
    ensure_cart_table_exists(shop, insales_id)
    table_name = build_cart_table_name(shop, insales_id)
    
    conn = create_shops_connection()
    cursor = conn.cursor()
    
    try:
        # Проверяем, есть ли уже такая позиция
        cursor.execute(f"""
            SELECT 1 FROM {table_name}
            WHERE user_id = %s AND variant_id = %s;
        """, (user_id, variant_id))
        existing = cursor.fetchone()
        
        if not existing:
            # ИСПРАВЛЯЕМ SQL ЗАПРОС - добавляем quantity в INSERT
            cursor.execute(f"""
                INSERT INTO {table_name} (
                    user_id, product_id, variant_id, variant_price,
                    image_0, variant_title, product_title, quantity
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, product_id, variant_id, variant_price,
                 image_0, variant_title, product_title, 1))  # Добавляем quantity = 1.
            conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_user_cart_db(user_id: str, shop: str, insales_id: str):
    """Получить корзину пользователя для конкретного магазина"""
    table_name = build_cart_table_name(shop, insales_id)
    conn = create_shops_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # Проверяем существование таблицы
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            );
        """, (table_name,))
        
        if not cursor.fetchone()[0]:
            return []
        
        cursor.execute(f"""
            SELECT product_id, variant_id, product_title, variant_title, 
                   variant_price, image_0, quantity
            FROM {table_name}
            WHERE user_id = %s;
        """, (str(user_id),))
        
        rows = cursor.fetchall()
        return rows if rows else []
    finally:
        cursor.close()
        conn.close()

def delete_from_user_cart_db(user_id: str, variant_id: int, shop: str, insales_id: str):
    """Удалить товар из корзины конкретного магазина"""
    table_name = build_cart_table_name(shop, insales_id)
    conn = create_shops_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"""
            DELETE FROM {table_name}
            WHERE user_id = %s AND variant_id = %s;
        """, (str(user_id), variant_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def bulk_update_cart_quantities(user_id: str, items: List[Dict], shop: str, insales_id: str):
    """Обновить количества товаров в корзине"""
    table_name = build_cart_table_name(shop, insales_id)
    conn = create_shops_connection()
    
    try:
        with conn.cursor() as cur:
            for it in items:
                cur.execute(f"""
                    UPDATE {table_name}
                    SET quantity = %s
                    WHERE user_id = %s AND variant_id = %s
                """, (int(it["quantity"]), str(user_id), int(it["variant_id"])))
        conn.commit()
    finally:
        conn.close()
