import numpy as np
from moviepy import (
    TextClip,
    CompositeVideoClip,
    vfx,
    ImageClip,
)
from dataclasses import dataclass


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


CONFIG = {
    "fontsize": 100,
    "font": "fonts/Arial.ttf",
    "final_color": (128, 128, 128)
}

phrases = [
    Phrase(
        text="Первая фраза",
        start=1.0,
        end=3.0,
        words=[
            Word("Первая", 1.0, 2.0),
            Word("фраза", 2.0, 3.0)
        ]
    ),
    Phrase(
        text="Вторая строка",
        start=3.0,
        end=6.0,
        words=[
            Word("Вторая", 3.0, 4.5),
            Word("строка", 4.5, 6.0)
        ]
    ),
    Phrase(
        text="Третья линия",
        start=6.0,
        end=9.0,
        words=[
            Word("Третья", 6.0, 7.5),
            Word("линия", 7.5, 9.0)
        ]
    ),
    Phrase(
        text="Четвертая запись",
        start=9.0,
        end=12.0,
        words=[
            Word("Четвертая", 9.0, 10.5),
            Word("запись", 10.5, 12.0)
        ]
    ),
    Phrase(
        text="Пятая строчка",
        start=12.0,
        end=15.0,
        words=[
            Word("Пятая", 12.0, 13.5),
            Word("строчка", 13.5, 15.0)
        ]
    )
]


def get_text_dimensions(text, fontsize, font):
    clip = TextClip(text=text, font_size=fontsize, font=font)
    return clip.w, clip.h


def create_phrase_animation(phrase: Phrase, config):
    char_clips = []
    current_pos = 0
    max_height = get_text_dimensions(phrase.text, config["fontsize"], config["font"])[1]
    adjusted_height = max_height + int(config["fontsize"] * 0.5)

    for word in phrase.words:
        char_duration = (word.end - word.start) / len(word.word)
        for i, char in enumerate(word.word):
            temp_clip = TextClip(text=char, font_size=config["fontsize"], font=config["font"])
            char_width = temp_clip.w

            clip = TextClip(
                text=char,
                color=(255, 255, 255, 255),
                font=config["font"],
                font_size=config["fontsize"],
                size=(char_width + 10, max_height + int(config["fontsize"] * 0.5)),
                transparent=True,
            )
            clip = clip.with_start(phrase.start)
            clip = clip.with_duration(phrase.end - phrase.start)
            clip = clip.with_position((current_pos, 0))
            char_clips.append(clip)

            clip = TextClip(
                text=char,
                color=(255, 165, 0, 255),
                font=config["font"],
                font_size=config["fontsize"],
                size=(char_width + 10, max_height + int(config["fontsize"] * 0.5)),
                transparent=True,
            )
            clip.mask = clip.mask.with_effects([vfx.FadeIn(0.2)])
            clip = clip.with_start(word.start + i * char_duration)
            clip = clip.with_duration(char_duration)
            clip = clip.with_duration(phrase.end - (word.start + i * char_duration))
            clip = clip.with_position((current_pos, 0))
            char_clips.append(clip)

            current_pos += char_width
        temp_clip = TextClip(text=" ", font_size=config["fontsize"], font=config["font"])
        current_pos += temp_clip.w
    return CompositeVideoClip(char_clips, size=(current_pos, adjusted_height))


def create_static_phrase_clip(phrase, config, duration):
    return TextClip(
        text=phrase.text,
        font=config["font"],
        font_size=config["fontsize"],
        color="white",
        size=(get_text_dimensions(phrase.text, config["fontsize"], config["font"])[0], None)
    ).with_duration(duration)


def create_background_with_image(image_path, size):
    w, h = size

    # Загружаем изображение
    image = ImageClip(image_path)

    # Масштабируем изображение, сохраняя пропорции
    if image.w / image.h > w / h:  # Если изображение шире пропорционально
        image = image.resized(width=w)
    else:  # Если изображение выше пропорционально
        image = image.resized(height=h)

    # Получаем массив фона (черный фон)
    bg_array = np.zeros((h, w, 3), dtype=np.uint8)

    # Вычисляем позицию для центрирования
    x_pos = (w - image.w) // 2
    y_pos = (h - image.h) // 2

    # Получаем массив изображения
    img_array = image.get_frame(0)

    # Вставляем изображение в фон
    bg_array[y_pos:y_pos + image.h, x_pos:x_pos + image.w] = img_array

    # Создаем финальный клип из массива
    final_clip = ImageClip(bg_array)

    return final_clip


def create_multi_phrase_video(phrases_list, config):
    total_duration = max(phrase.end for phrase in phrases_list)

    cover_image = "media/muziki_cover.jpg"

    # Загружаем фоновое изображение
    background = create_background_with_image(cover_image, (1920, 1080)).with_duration(total_duration)

    clips = []
    # Вычисляем высоту строки с запасом
    line_height = get_text_dimensions(phrases_list[0].text, config["fontsize"], config["font"])[1] + int(
        config["fontsize"] * 0.5) + 10

    # Верхняя линия: статический клип для первой фразы с 0 до её start
    if phrases_list[0].start > 0:
        static_top = create_static_phrase_clip(phrases_list[0], config, phrases_list[0].start).with_position(
            ('center', 0))
        clips.append(static_top)

    # Верхняя линия: анимированные клипы для каждой фразы
    for phrase in phrases_list:
        animated_clip = create_phrase_animation(phrase, config).with_position(('center', 0))
        clips.append(animated_clip)

    # Нижняя линия: статические клипы для следующих фраз
    if len(phrases_list) > 1:
        # Начальный статический клип для второй фразы с 0 до её start
        static_bottom_initial = create_static_phrase_clip(phrases_list[1], config, phrases_list[1].start).with_position(
            ('center', line_height))
        clips.append(static_bottom_initial)

        # Статические клипы для всех последующих фраз
        for i in range(1, len(phrases_list) - 1):
            next_phrase = phrases_list[i + 1]
            start_time = phrases_list[i].start
            end_time = next_phrase.start
            duration = end_time - start_time
            if duration > 0:
                static_bottom = create_static_phrase_clip(next_phrase, config, duration).with_position(
                    ('center', line_height)).with_start(start_time)
                clips.append(static_bottom)

    # Определяем размеры композиции фраз
    max_width = max(get_text_dimensions(phrase.text, config["fontsize"], config["font"])[0] for phrase in phrases_list)
    total_height = 2 * line_height

    # Создаем композицию фраз
    phrase_composite = CompositeVideoClip(clips, size=(max_width, total_height)).with_duration(total_duration)

    # Центрируем композицию фраз в кадре 1920x1080
    pos_x = (1920 - max_width) / 2
    pos_y = (1080 - total_height) / 2
    phrase_composite = phrase_composite.with_position((pos_x, pos_y))

    # Создаем финальный клип с фоном и фразами
    final_clip = CompositeVideoClip([background, phrase_composite], size=(1920, 1080))

    return final_clip


# Генерируем видео
video = create_multi_phrase_video(phrases, CONFIG)
video.write_videofile(
    "multi_phrase_with_background.mp4",
    fps=12
)
