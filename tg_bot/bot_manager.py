import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage
import psycopg2
from secret import Db
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Message

# http://127.0.0.1:8080/main/1030167/4forms.ru
# https://insales-tg-shop.ru/main/1030167/4forms.ru
# https://github.com/Fis9000/insales-telegram-shop/actions
# ngrok http http://localhost:8080

# local = "8039632943:AAF2vXsg2lI9a1ESm2z9wHuAADbEVtg0Eqo"
# prod = "8372156969:AAHnESu2tAy6pRdOyrjTijCb4OetvZkxlOs"

class BotManager:
    def __init__(self):
        self.active_bots = {}

    def create_connection(self):
        return psycopg2.connect(
            host=Db.host, database=Db.database, user=Db.user, password=Db.password
        )

    async def start_bot(self, insales_id: int, shop: str, bot_token: str, force_restart: bool=False) -> bool:
        bot_key = f"{insales_id}_{shop}"

        # если уже есть — по желанию перезапустить
        if bot_key in self.active_bots:
            if not force_restart:
                print(f"Бот для {bot_key} уже запущен")
                return True
            await self.stop_bot(insales_id, shop)

        try:
            bot = Bot(token=bot_token)
            
            # ⭐ ДОБАВЬТЕ ЭТУ СТРОКУ - удаление webhook перед polling
            await bot.delete_webhook(drop_pending_updates=True)
            
            storage = MemoryStorage()
            dp = Dispatcher(storage=storage)
            router = self._build_router(insales_id, shop)
            dp.include_router(router)

            self.active_bots[bot_key] = {
                "bot": bot,
                "dispatcher": dp,
                "storage": storage,
                "router": router,
                "task": None,
            }

            async def _poll():
                try:
                    await dp.start_polling(bot, handle_signals=False)
                except Exception as e:
                    print(f"Ошибка поллинга для {bot_key}: {e}")

            task = asyncio.create_task(_poll(), name=f"poll_{bot_key}")
            self.active_bots[bot_key]["task"] = task

            print(f"✅ Запущен бот для {shop}")
            return True
        except Exception as e:
            print(f"❌ Ошибка запуска бота для {bot_key}: {e}")
            # откат кэша если частично создалось
            self.active_bots.pop(bot_key, None)
            return False

    def _build_router(self, insales_id: int, shop: str) -> Router:
        r = Router()
        web_app_url = WebAppInfo(url=f"https://93ac17a4abfe.ngrok-free.app/main/{insales_id}/{shop}")
        # web_app_url = WebAppInfo(url=f"https://insales-tg-shop.ru/main/{insales_id}/{shop}")
        @r.message(Command("start"))
        async def cmd_start(message: Message):
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Каталог", web_app=web_app_url)]
            ])
            welcome_text = await self._get_welcome_text(insales_id, shop)
            await message.answer(welcome_text, reply_markup=kb)

        return r

    async def _get_welcome_text(self, insales_id, shop) -> str:
        try:
            conn = self.create_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT welcome_text FROM users_tb WHERE insales_id = %s AND shop = %s",
                (insales_id, shop)
            )
            row = cur.fetchone()
            cur.close()
            conn.close()
            
            if row and row[0]:  # row[0] - первый элемент кортежа
                return row[0]
            else:
                return "Добро пожаловать в наш магазин! 🛍️"
                
        except Exception as e:
            print(f"_get_welcome_text error: {e}")
            return "Добро пожаловать в наш магазин! 🛍️"

    async def _stop_polling_safe(self, dp: Dispatcher):
        try:
            await dp.stop_polling()
        except Exception as e:
            print(f"stop_polling error: {e}")

    async def stop_bot(self, insales_id: int, shop: str):
        bot_key = f"{insales_id}_{shop}"
        data = self.active_bots.pop(bot_key, None)
        if not data:
            return
        # попросить dp остановиться
        await self._stop_polling_safe(data["dispatcher"])
        # закрыть сессию бота
        try:
            await data["bot"].session.close()
        except Exception as e:
            print(f"bot session close error: {e}")
        # дождаться задачи, если есть
        task = data.get("task")
        if task and not task.done():
            task.cancel()
            try:
                await task
            except Exception:
                pass
        print(f"⏹️ Остановлен бот для {shop}")

    async def initialize_all_bots(self):
        try:
            conn = self.create_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT insales_id, shop, token FROM users_tb WHERE token IS NOT NULL AND is_active = TRUE"
            )
            bots = cur.fetchall()
            cur.close()
            conn.close()

            print(f"🔄 Запускаем {len(bots)} ботов...")
            await asyncio.gather(*[
                self.start_bot(insales_id, shop, token, force_restart=False)
                for insales_id, shop, token in bots
            ])
        except Exception as e:
            print(f"❌ Ошибка инициализации ботов: {e}")

    async def stop_all(self):
        keys = list(self.active_bots.keys())
        await asyncio.gather(*[
            self.stop_bot(int(k.split("_", 1)), k.split("_", 1)[1])
            for k in keys
        ])
