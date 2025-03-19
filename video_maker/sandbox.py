from moviepy import *
import numpy as np
from functools import partial
from dataclasses import dataclass


# Описание структур данных
@dataclass(slots=True)
class Word:
    word: str
    start: float
    end: float


@dataclass(slots=True)
class Phrase:
    text: str
    start: float
    end: float
    words: list[Word]


# Конфигурация
CONFIG = {
    "fontsize": 100,
    "font": "fonts/Arial.ttf",
    "final_color": (128, 128, 128)
}

# Пример данных
phrase = Phrase(
    text="Пример, текста!",
    start=0.0,
    end=5.0,
    words=[
        Word("Пример", 0.0, 1.0),
        Word("текста", 1.0, 5.0)
    ]
)


# Функция получения размеров текста
def get_text_dimensions(text, fontsize, font):
    clip = TextClip(text=text, font_size=fontsize, font=font)
    return clip.w, clip.h  # Используем .w и .h для точности


# Функция создания кадра для символа
def create_char_frame(char, char_width, max_height, font, fontsize):
    def frame_func(t, start_time, end_time):
        alpha = np.clip((t - start_time) / (end_time - start_time), 0, 1) if end_time > start_time else 1
        gray_level = int(255 - alpha * (255 - 128))
        color = (gray_level, gray_level, gray_level)
        clip = TextClip(
            text=char,
            font_size=fontsize,
            color=color,
            font=font,
            size=(char_width, max_height + int(fontsize * 0.5))  # Добавляем запас снизу
        )
        return clip.get_frame(0)

    return frame_func


# Функция создания кадра для пробела (статический белый)
def create_space_frame(char_width, max_height, font, fontsize):
    def frame_func(t):
        clip = TextClip(
            text=" ",
            font_size=fontsize,
            color="white",
            font=font,
            size=(char_width, max_height + int(fontsize * 0.5))  # Тот же запас
        )
        return clip.get_frame(0)

    return frame_func


# Функция расчета времени начала и конца для символа в слове
def calculate_char_times(word_data, char_index, char_count, phrase_start):
    word_duration = word_data.end - word_data.start
    absolute_start = phrase_start + word_data.start
    start_time = absolute_start + (char_index / char_count) * word_duration
    end_time = absolute_start + ((char_index + 1) / char_count) * word_duration
    return start_time, end_time


# Функция создания клипа для символа
def create_char_clip(char, char_width, max_height, start_time, end_time, font, fontsize, duration):
    frame_maker = create_char_frame(char, char_width, max_height, font, fontsize)
    return VideoClip(
        partial(frame_maker, start_time=start_time, end_time=end_time),
        duration=duration
    )


# Основная функция создания анимации
def create_phrase_animation(phrase: Phrase, config):
    # Получаем размеры полной фразы
    max_width, max_height = get_text_dimensions(phrase.text, config["fontsize"], config["font"])
    phrase_duration = phrase.end - phrase.start
    char_width = max_width // len(phrase.text)

    # Увеличиваем высоту для всего клипа, чтобы вместить выносные элементы
    adjusted_height = max_height + int(config["fontsize"] * 0.5)

    # Создаем клипы для каждого символа
    char_clips = []
    current_pos = 0
    word_idx = 0
    word_char_idx = 0

    for i, char in enumerate(phrase.text):
        if word_idx >= len(phrase.words):
            break

        current_word = phrase.words[word_idx]
        word_text = current_word.word

        # Если символ — пробел
        if char.isspace():
            clip = VideoClip(
                create_space_frame(char_width, max_height, config["font"], config["fontsize"]),
                duration=phrase_duration
            ).with_position((current_pos, 0))
            char_clips.append(clip)
        # Если символ принадлежит текущему слову
        elif word_char_idx < len(word_text) and char == word_text[word_char_idx]:
            start_time, end_time = calculate_char_times(current_word, word_char_idx, len(word_text), phrase.start)
            clip = create_char_clip(
                char=char,
                char_width=char_width,
                max_height=max_height,
                start_time=start_time,
                end_time=end_time,
                font=config["font"],
                fontsize=config["fontsize"],
                duration=phrase_duration
            ).with_position((current_pos, 0))
            char_clips.append(clip)
            word_char_idx += 1
            if word_char_idx >= len(word_text):
                word_idx += 1
                word_char_idx = 0
        # Если символ — знак препинания
        else:
            prev_word = phrase.words[word_idx - 1] if word_idx > 0 else current_word
            start_time, end_time = calculate_char_times(prev_word, len(prev_word.word) - 1, len(prev_word.word),
                                                        phrase.start)
            clip = create_char_clip(
                char=char,
                char_width=char_width,
                max_height=max_height,
                start_time=start_time,
                end_time=end_time,
                font=config["font"],
                fontsize=config["fontsize"],
                duration=phrase_duration
            ).with_position((current_pos, 0))
            char_clips.append(clip)

        current_pos += char_width

    # Компонуем все символы в итоговый клип с увеличенной высотой
    return CompositeVideoClip(char_clips, size=(max_width, adjusted_height))


# Выполнение
animation = create_phrase_animation(phrase, CONFIG)
animation.write_videofile(
    "phrase_fade_letters.mp4",
    fps=30
)
