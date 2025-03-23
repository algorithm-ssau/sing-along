import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command


logging.basicConfig(level=logging.INFO)
load_dotenv()
API_KEY = os.getenv("BOT_API_KEY")
bot = Bot(token=API_KEY)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Hello, World!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())