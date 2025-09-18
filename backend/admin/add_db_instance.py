import asyncio
import gzip
import http.client
from io import BytesIO
import json

async def add_db_instance(user_name):
    """Добавление инстанса БД для пользователя модуля"""
    try:
        conn = http.client.HTTPSConnection("api.timeweb.cloud")
        payload = json.dumps({
        "name": f"{user_name}"
        })
        headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCIsImtpZCI6IjFrYnhacFJNQGJSI0tSbE1xS1lqIn0.eyJ1c2VyIjoidmM1NDgyMCIsInR5cGUiOiJhcGlfa2V5IiwiYXBpX2tleV9pZCI6IjRmY2I0NGFiLWYxMzYtNGNkMS1iM2NmLTRhZmNlNzBkNTM1ZSIsImlhdCI6MTc1NzMzODc3NH0.U4stCuaQSCzcYp4LiAJCkrkeUAOkJxpYolOadYyQKwQCOYfmVcPJW1O4zf4n4mHYY8I4s6dCteync51TP8E8_nmC_iwhpjKbe_k3k9GxJpUhdqRAjE3X77fSmT7rbV-o0ue_jx1_7n9ufMNvhMI8bCQ4dSrgXzZH8QVnWuuConsI3Pce5qIQGNMqK8AZBYKxhbGVr6U3S-1ZIuMezntuMgtPhtvdc1b7uLzzAD2h87h6w6qBT9gwicTF10xFZiplLbDPfEWUo23IBKqL5_ewxqpn99pc1nLzTO4jCOtUtwT2Oz0LquT-7Gb-t1fRZN04A-9MzXsCEMM11eyGd-UvsinuBaVNeoMb8SCVjdWKNEpWnuhI8laEJozE3A7AyxOP1zEdxSXHMgCY3nHVi8JJO6paGK0h-pGXrh57kQQXq9Ak9EVgbE5CHyk6tB39Xftx16SRm1-kCKa3uJGShYkVpZc9yjZnEbUZXZhdeEhfK-GMWoiQbkN8JE6fstaGstSO'
        }
        conn.request("POST", "/api/v1/databases/4085227/instances", payload, headers)
        res = conn.getresponse()
        data = res.read()
        
        if res.getheader('Content-Encoding') == 'gzip':
            buf = BytesIO(data)
            data = gzip.decompress(buf.read())

        json_string = data.decode("utf-8")
        json_data = json.loads(json_string)

        instance_id = json_data["instance"]["id"]

    except Exception as e:
        print(f"add_db_cluster: {e}")
        return "error"
    
    await asyncio.sleep(5)
    await add_db_instance_privileges(instance_id)

async def add_db_instance_privileges(instance_id):
    try:
        """Добавление привелегий для созданного кластера"""
        conn = http.client.HTTPSConnection("api.timeweb.cloud")
        payload = json.dumps({
        "privileges": [
            "SELECT",
            "INSERT",
            "UPDATE",
            "DELETE",
            "CREATE",
            "TRUNCATE",
            "REFERENCES",
            "TRIGGER",
            "TEMPORARY",
            "CREATEDB",
            "CREATEROLE"
        ],
        "instance_id": instance_id
        })
        headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCIsImtpZCI6IjFrYnhacFJNQGJSI0tSbE1xS1lqIn0.eyJ1c2VyIjoidmM1NDgyMCIsInR5cGUiOiJhcGlfa2V5IiwiYXBpX2tleV9pZCI6IjRmY2I0NGFiLWYxMzYtNGNkMS1iM2NmLTRhZmNlNzBkNTM1ZSIsImlhdCI6MTc1NzMzODc3NH0.U4stCuaQSCzcYp4LiAJCkrkeUAOkJxpYolOadYyQKwQCOYfmVcPJW1O4zf4n4mHYY8I4s6dCteync51TP8E8_nmC_iwhpjKbe_k3k9GxJpUhdqRAjE3X77fSmT7rbV-o0ue_jx1_7n9ufMNvhMI8bCQ4dSrgXzZH8QVnWuuConsI3Pce5qIQGNMqK8AZBYKxhbGVr6U3S-1ZIuMezntuMgtPhtvdc1b7uLzzAD2h87h6w6qBT9gwicTF10xFZiplLbDPfEWUo23IBKqL5_ewxqpn99pc1nLzTO4jCOtUtwT2Oz0LquT-7Gb-t1fRZN04A-9MzXsCEMM11eyGd-UvsinuBaVNeoMb8SCVjdWKNEpWnuhI8laEJozE3A7AyxOP1zEdxSXHMgCY3nHVi8JJO6paGK0h-pGXrh57kQQXq9Ak9EVgbE5CHyk6tB39Xftx16SRm1-kCKa3uJGShYkVpZc9yjZnEbUZXZhdeEhfK-GMWoiQbkN8JE6fstaGstSO'
        }
        conn.request("PATCH", "/api/v1/databases/4085227/admins/295439", payload, headers)
        res = conn.getresponse()
        data = res.read()

        if res.getheader('Content-Encoding') == 'gzip':
            buf = BytesIO(data)
            data = gzip.decompress(buf.read())

        json_string = data.decode("utf-8")
        json_data = json.loads(json_string)

    except Exception as e:
        print(f"add_db_cluster_privileges: {e}")
        return "error"    
