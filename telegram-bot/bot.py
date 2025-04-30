import asyncio
import logging
import os
from datetime import datetime

from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
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
    audio = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Песня", callback_data="song"))
    builder.row(types.InlineKeyboardButton(text="Информация", callback_data="info"))
    builder.row(types.InlineKeyboardButton(text="Видео", callback_data="video"))
    await message.answer("Hello, World!", reply_markup=builder.as_markup())

@dp.message(Command("info"))
@dp.callback_query(F.data == "info")
async def cmd_info(message: types.Message, started_at: str):
    if not data["song_name"]:
        await bot.send_message(chat_id=message.from_user.id, text=f"Бот запущен {started_at}\nТекущей песни нет")
        return
    await bot.send_message(chat_id=message.from_user.id, text=f"Бот запущен {started_at}\nТекущая песня: {data['song_name']}")

@dp.message(Command("video"))
@dp.callback_query(F.data == "video")
async def cmd_video(message: types.Message):
    await bot.send_video(chat_id=message.from_user.id, video="https://avtshare01.rz.tu-ilmenau.de/avt-vqdb-uhd-1/test_1/segments/bigbuck_bunny_8bit_15000kbps_1080p_60.0fps_h264.mp4")

@dp.message(Command("song"))
@dp.callback_query(F.data == "song")
async def cmd_song(message: types.Message, state: FSMContext):
    await state.set_state(SongStates.name)
    await bot.send_message(chat_id=message.from_user.id, text=f"Введите название песни:")

@dp.message(StateFilter(None), Command("cancel"))
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info("Отмeнено состояние %r", current_state)
    await state.clear()
    await message.reply("Отмена.", reply_markup=types.ReplyKeyboardRemove())

@dp.message(StateFilter(SongStates.name))
async def enter_song_name(message: types.Message, state: FSMContext):
    data["song_name"] = message.text
    logging.info("Название песние %r", data["song_name"])
    await state.set_state(SongStates.audio)
    await bot.send_message(chat_id=message.from_user.id, text=f"Прикрепите аудио файл")

@dp.message(StateFilter(SongStates.audio))
async def attach_audio(message: types.Message, state: FSMContext):
    audio_file_id = message.audio.file_id
    await bot.send_audio(chat_id=message.from_user.id, audio=audio_file_id)
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())