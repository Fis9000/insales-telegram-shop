# https://github.com/Fis9000/insales-telegram-shop/actions

echo "Останавливаем процесс на порту 8080..."
lsof -ti:8080 | xargs -r kill -9

cd /root/insales-telegram-shop || { echo "Не удалось перейти в insales-telegram-shop"; exit 1; }

echo "Устанавливаем зависимости..."
pip3 install -r requirements.txt

echo "Запускаем uvicorn..."
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8080 > insales-telegram-shop.log 2>&1 &

echo "Перезапуск insales-telegram-shop завершён."