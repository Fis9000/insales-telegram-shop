import psycopg2
from psycopg2 import sql
from secret import Db

def add_db_tables_collections_tb(db_name, prefix):
    conn = None
    try:
        conn = psycopg2.connect(
            host=Db.host,
            database=db_name,
            user=Db.user,
            password=Db.password
        )
        cursor = conn.cursor()

        safe_prefix = prefix.replace('.', '_').replace('-', '_').replace(' ', '_')
        safe_safe_prefix = f"shop_{safe_prefix}"

        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {safe_safe_prefix}_collections_tb (
            id BIGINT PRIMARY KEY,
            title TEXT,
            position INTEGER,
            is_hidden BOOL,
            updated_at TIMESTAMP,
            parent_id BIGINT,
            active BOOL
        );
        """
        cursor.execute(create_table_query)
        conn.commit()

        print(f"Таблица '{prefix}_collections_tb' успешно создана или уже существует.")
        return True

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Ошибка при работе с PostgreSQL: {error}")
        return False

    finally:
        if conn is not None:
            cursor.close()
            conn.close()

def add_db_tables_products_tb(db_name, prefix):
    conn = None
    try:
        conn = psycopg2.connect(
            host=Db.host,
            database=db_name,
            user=Db.user,
            password=Db.password
        )
        cursor = conn.cursor()

        safe_prefix = prefix.replace('.', '_').replace('-', '_').replace(' ', '_')
        safe_safe_prefix = f"shop_{safe_prefix}"

        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {safe_safe_prefix}_products_tb (
            product_id BIGINT PRIMARY KEY,
            title TEXT,
            description TEXT,
            image_0 TEXT,
            image_1 TEXT,
            image_2 TEXT,
            base_price NUMERIC,
            old_price NUMERIC,
            structure TEXT,
            is_hidden BOOL,
            updated_date TIMESTAMP,
            is_collection_new BOOL,
            is_collection_sale BOOL,
            image_3 TEXT,
            image_4 TEXT,
            image_5 TEXT,
            image_6 TEXT,
            image_7 TEXT,
            image_8 TEXT,
            collection_ids BIGINT[],
            available BOOL,
            canonical_url_collection_id BIGINT
        );
        """
        cursor.execute(create_table_query)
        conn.commit()

        print(f"Таблица '{prefix}_products_tb' успешно создана или уже существует.")
        return True

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Ошибка при работе с PostgreSQL: {error}")
        return False

    finally:
        if conn is not None:
            cursor.close()
            conn.close()

def add_db_tables_variants_tb(db_name, prefix):
    conn = None
    try:
        conn = psycopg2.connect(
            host=Db.host,
            database=db_name,
            user=Db.user,
            password=Db.password
        )
        cursor = conn.cursor()

        safe_prefix = prefix.replace('.', '_').replace('-', '_').replace(' ', '_')
        safe_safe_prefix = f"shop_{safe_prefix}"

        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {safe_safe_prefix}_variants_tb (
            product_id BIGINT,
            variant_id BIGINT PRIMARY KEY,
            title TEXT,
            updated_date TIMESTAMP,
            variant_price NUMERIC
        );
        """
        cursor.execute(create_table_query)
        conn.commit()

        print(f"Таблица '{prefix}_variants_tb' успешно создана или уже существует.")
        return True

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Ошибка при работе с PostgreSQL: {error}")
        return False

    finally:
        if conn is not None:
            cursor.close()
            conn.close()

def add_db_tables_user_cart_tb(db_name, prefix):
    conn = None
    try:
        conn = psycopg2.connect(
            host=Db.host,
            database=db_name,
            user=Db.user,
            password=Db.password
        )
        cursor = conn.cursor()

        safe_prefix = prefix.replace('.', '_').replace('-', '_').replace(' ', '_')
        safe_safe_prefix = f"shop_{safe_prefix}"

        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {safe_safe_prefix}_user_cart_tb (
            user_id BIGINT,
            product_id BIGINT,
            variant_id BIGINT,
            variant_price NUMERIC,
            image_0 TEXT,
            variant_title TEXT,
            product_title TEXT,
            quantity BIGINT
        );
        """
        cursor.execute(create_table_query)
        conn.commit()

        print(f"Таблица '{prefix}_user_cart_tb' успешно создана или уже существует.")
        return True

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Ошибка при работе с PostgreSQL: {error}")
        return False

