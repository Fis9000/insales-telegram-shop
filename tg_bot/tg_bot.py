import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

# http://http://127.0.0.1:8080/main
# https://
# https://github.com/Fis9000/insales-telegram-shop/actions
# ngrok http http://localhost:8080

"""Локалка"""
TELEGRAM_TOKEN = "8039632943:AAF2vXsg2lI9a1ESm2z9wHuAADbEVtg0Eqo"
web_app_url = WebAppInfo(url="https://534729c562be.ngrok-free.app/4f-tg-shop")

"""Прод"""
# TELEGRAM_TOKEN ="" 8372156969:AAHnESu2tAy6pRdOyrjTijCb4OetvZkxlOs"
# web_app_url = WebAppInfo(url="https://shop.4forms-tech.ru/4f-tg-shop")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

raw_text  = "bot_welcome_text"
bot_welcome_text = raw_text.replace("\\n", "\n")

inline_keyboard = [
    [
        InlineKeyboardButton(
            text="Каталог",
            web_app=web_app_url
        )
    ],
]

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer(bot_welcome_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_keyboard))  # inline кнопка "Каталог" 

async def incoming_messages():
    await dp.start_polling(bot)

async def tg_shop_start_bot():
    await incoming_messages()
