from fastapi import APIRouter, HTTPException, Request
from .collections_manager import fetch_collections_from_insales, save_collections_to_shop_db, create_connection

router = APIRouter()

@router.post("/reset_collections")
async def reset_collections(request: Request):
    try:
        print("reset_collections endpoint called")

        data = await request.json()
        insales_id_raw = data.get("insales_id")
        shop = (data.get("shop") or "").strip()
        if not insales_id_raw or not shop:
            raise HTTPException(status_code=400, detail="insales_id и shop обязательны")
        try:
            insales_id = int(insales_id_raw)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="insales_id должен быть числом")

        conn = create_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT insales_id, shop, inales_api_token
            FROM users_tb
            WHERE insales_id = %s AND shop = %s
            LIMIT 1
            """,
            (insales_id, shop)
        )
        result = cur.fetchone()
        cur.close()
        conn.close()

        print(f"Database result: {result}")
        if not result:
            raise HTTPException(status_code=404, detail="Настройки не найдены для указанного магазина")

        insales_id_db, shop_db, inales_api_token = result
        if not inales_api_token or not shop_db:
            raise HTTPException(status_code=404, detail="Не найден токен или shop для указанного магазина")

        print(f"Processing for insales_id: {insales_id_db}, shop: {shop_db}")

        print("Fetching collections from InSales...")
        collections = await fetch_collections_from_insales(shop_db, inales_api_token)
        if not collections:
            raise HTTPException(status_code=404, detail="Коллекции не найдены")
        print(f"Fetched {len(collections)} collections")

        print("Saving collections to shop database...")
        success = await save_collections_to_shop_db(shop_db, insales_id_db, collections)

        if success:
            print("Collections saved successfully")
            return {
                "status": "success",
                "message": f"Синхронизировано {len(collections)} коллекций",
                "count": len(collections)
            }
        else:
            print("Failed to save collections")
            raise HTTPException(status_code=500, detail="Ошибка сохранения коллекций")

    except HTTPException as he:
        print(f"HTTPException: {he.detail}")
        raise
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка синхронизации: {str(e)}")
