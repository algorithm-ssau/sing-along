import asyncio
import logging
import os
from datetime import datetime

from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.filters.state import State, StatesGroup, StateFilter

logging.basicConfig(level=logging.INFO)
load_dotenv()
API_KEY = os.getenv("BOT_API_KEY")
bot = Bot(token=API_KEY)
dp = Dispatcher()
dp["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
data = {"song_name": ""}

class SongStates(StatesGroup):
    default = State()
    name = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Hello, World!")

@dp.message(Command("info"))
async def cmd_info(message: types.Message, started_at: str):
    if not data["song_name"]:
        await message.answer(f"Бот запущен {started_at}\nТекущей песни нет")
        return
    await message.answer(f"Бот запущен {started_at}\nТекущая песня: {data['song_name']}")

@dp.message(Command("song"))
async def cmd_song(message: types.Message, state: FSMContext):
    await state.set_state(SongStates.name)
    await message.answer(f"Введите название песни:")

@dp.message(StateFilter(SongStates.name))
async def enter_song_name(message: types.Message, state: FSMContext):
    data["song_name"] = message.text
    logging.info("Название песние %r", data["song_name"])
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())