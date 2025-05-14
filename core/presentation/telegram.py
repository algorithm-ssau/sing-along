import asyncio
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.filters.state import State, StatesGroup, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

from core.infrastructure.separation.spleeter_ai import SpleeterSeparator
from core.infrastructure.text_generation.genius import GeniusTextScrapper
from core.infrastructure.text_generation.mock import MockTextScrapper
from core.infrastructure.timestamp_linking.per_phrase_alignment_linking import PhraseGrabberTextAlignmentLinker
from core.infrastructure.video_maker.ffmpeg_video_maker import FfmpegVideoMaker
from core.infrastructure.voice_recognition.whisper_ai import WhisperRecognizer

logging.basicConfig(level=logging.INFO)
load_dotenv()
API_KEY = os.getenv("BOT_API_KEY")
bot = Bot(token=API_KEY)
dp = Dispatcher()
dp["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
USER_DATA = Path("user_data")


class SongStates(StatesGroup):
    default = State()
    name = State()
    audio = State()
    cover = State()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Создать караоке", callback_data="song"))
    start_info = """Данный бот предназначен для автоматической генерации караоке-видео"""
    await message.answer(start_info, reply_markup=builder.as_markup())


@dp.message(Command("info"))
@dp.callback_query(F.data == "info")
async def cmd_info(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    song_name = user_data.get("song_name", None)

    if song_name is None:
        await bot.send_message(
            chat_id=callback.from_user.id,
            text=f"Бот запущен {dp['started_at']}\nТекущей песни нет",
        )
        return

    await bot.send_message(
        chat_id=callback.from_user.id,
        text=f"Бот запущен {dp['started_at']}\nТекущая песня: {song_name}",
    )


@dp.message(Command("video"))
@dp.callback_query(F.data == "video")
async def cmd_video(callback: types.CallbackQuery):
    video_path = "Фазенда - Мужики_karaoke.mp4"
    video_file = FSInputFile(path=video_path)

    await bot.send_video(chat_id=callback.from_user.id, video=video_file)


@dp.message(Command("song"))
@dp.callback_query(F.data == "song")
async def cmd_song(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SongStates.name)
    await bot.send_message(
        chat_id=callback.from_user.id, text=f"Введите исполнителя и название песни \n"
                                            f"(например Rick Astley - Never Gonna Give You Up):"
    )


@dp.message(StateFilter(None), Command("cancel"))
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info("Отменено состояние %r", current_state)
    await state.clear()
    await message.reply("Отмена.", reply_markup=types.ReplyKeyboardRemove())


@dp.message(StateFilter(SongStates.name))
async def enter_song_name(message: types.Message, state: FSMContext):
    await state.update_data(
        song_name=message.text
    )  # Сохраняем название песни в контексте
    logging.info("Название песни: %r", message.text)
    await state.set_state(SongStates.audio)
    await bot.send_message(chat_id=message.from_user.id, text=f"Прикрепите аудио файл:")


@dp.message(StateFilter(SongStates.audio))
async def attach_audio(message: types.Message, state: FSMContext):
    audio_file_id = message.audio.file_id
    logging.info("Получен audio file ID: %r", audio_file_id)

    audio_file = await bot.get_file(audio_file_id)
    file_extension = audio_file.file_path.rsplit(".", 1)[-1]
    destination = USER_DATA / str(message.from_user.id) / f"audio.{file_extension}"
    shutil.rmtree(str(destination.parent), ignore_errors=True)
    destination.parent.mkdir()
    await bot.download_file(audio_file.file_path, destination)
    await state.set_state(SongStates.cover)
    await bot.send_message(chat_id=message.from_user.id, text=f"Прикрепите фоновое изображение:")


@dp.message(StateFilter(SongStates.cover))
async def attach_cover(message: types.Message, state: FSMContext):
    if message.content_type == 'photo':
        cover_file_id = message.photo[-1].file_id
    elif message.content_type == 'document':
        cover_file_id = message.document.file_id
    else:
        await bot.send_message(
            chat_id=message.from_user.id,
            text=f"Необходима картинка",
        )
        return
    logging.info("Получен cover file ID: %r", cover_file_id)

    cover_file = await bot.get_file(cover_file_id)
    file_extension = cover_file.file_path.rsplit(".", 1)[-1]
    user_folder = USER_DATA / str(message.from_user.id)
    destination = user_folder / f"cover.{file_extension}"
    await bot.download_file(cover_file.file_path, destination)
    await bot.send_message(
        chat_id=message.from_user.id,
        text=f"Спасибо за предоставленные файлы, приступаю к созданию караоке. Примерное время ожидания - 10-15 минут",
    )
    user_data = await state.get_data()
    song_name: str = user_data["song_name"]
    audio_file = next(user_folder.glob("audio.*"))
    await make_a_video(
        message=message,
        song_title=song_name,
        audio_file=audio_file,
        cover_image_file=destination,
    )
    await state.clear()


async def make_a_video(
    message: types.Message, song_title: str, audio_file: Path, cover_image_file: Path
):
    audio_separator = SpleeterSeparator()
    text_generator = GeniusTextScrapper()
    voice_recognizer = WhisperRecognizer()
    timestamp_linker = PhraseGrabberTextAlignmentLinker()
    video_maker = FfmpegVideoMaker()
    bot_message = await bot.send_message(
        chat_id=message.from_user.id,
        text="🔵Получение текста песни...",
    )
    song_text = text_generator.get_text_for_a_song(song_title=song_title)
    await bot_message.edit_text("✅Текст песни получен")
    bot_message = await bot.send_message(
        chat_id=message.from_user.id,
        text="🔵Разделение вокала и инструментала...",
    )
    separation_result = audio_separator.separate_into_vocals_and_music(
        audio_file=audio_file
    )
    await bot_message.edit_text("✅Вокал и инструментал разделены")
    bot_message = await bot.send_message(
        chat_id=message.from_user.id,
        text="🔵Получение временных меток...",
    )
    recognized_phrases = voice_recognizer.get_text_from_vocals(
        vocals=separation_result.vocals
    )
    timestamped_phrases = timestamp_linker.link_timestamps_to_song_text(
        full_text=song_text, phrases=recognized_phrases
    )
    await bot_message.edit_text("✅Временные метки получены")
    bot_message = await bot.send_message(
        chat_id=message.from_user.id,
        text="🔵Отрисовка видео...",
    )
    video_path = video_maker.compile_video(
        song_title=song_title,
        cover_image=cover_image_file,
        back_track=separation_result.back_track,
        timestamped_phrases=timestamped_phrases,
    )
    await bot_message.edit_text(text="✅Видео отрисовано")
    video_file = FSInputFile(path=video_path, filename=f"{song_title}.mp4")
    await bot.send_video(chat_id=message.from_user.id, video=video_file)
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Создать караоке", callback_data="song"))
    await bot.send_message(chat_id=message.from_user.id, text="Продолжим?", reply_markup=builder.as_markup())


async def main():
    USER_DATA.mkdir(exist_ok=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
