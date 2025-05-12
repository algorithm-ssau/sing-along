import json
from pathlib import Path

import adaptix
import numpy as np
from moviepy import AudioFileClip, ImageClip, CompositeVideoClip, TextClip, vfx, ColorClip

from core.application.dto import AudioPath, ImagePath, VideoPath
from core.application.video_maker import VideoMaker
from core.application.voice_recognition import Phrase


class FfmpegVideoMaker(VideoMaker):
    inactive_color = (255, 255, 255, 255)
    active_color = (255, 165, 0, 255)
    back_color = (0, 0, 0, 128)
    font = "fonts/Arial.ttf"
    font_size = 40
    output_size = (1920, 1080)
    fps = 12

    def create_background_with_image(self, image_path, size):
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

    def create_static_phrase_clip(self, phrase, duration):
        width, max_height = self.get_text_dimensions(phrase.text)
        adjusted_height = max_height + int(self.font_size * 0.5)
        return TextClip(
            text=phrase.text,
            font=self.font,
            font_size=self.font_size,
            color=self.inactive_color,
            bg_color=self.back_color,
            size=(width + 10, adjusted_height)
        ).with_duration(duration)

    def create_phrase_animation(self, phrase: Phrase):
        char_clips = []
        current_pos = 0
        max_height = self.get_text_dimensions(phrase.text)[1]
        adjusted_height = max_height + int(self.font_size * 0.5)

        for word in phrase.words:
            char_duration = (word.end - word.start) / len(word.word)

            word_char_clips = []
            for i, char in enumerate(word.word):
                temp_clip = TextClip(text=char, font_size=self.font_size, font=self.font)
                char_width = temp_clip.w

                clip = TextClip(
                    text=char,
                    color=self.inactive_color,
                    font=self.font,
                    font_size=self.font_size,
                    size=(char_width + 10, max_height + int(self.font_size * 0.5)),
                    transparent=True,
                )
                clip = clip.with_start(phrase.start)
                clip = clip.with_duration(phrase.end - phrase.start)
                clip = clip.with_position((current_pos, 0))
                word_char_clips.append(clip)

                clip = TextClip(
                    text=char,
                    color=self.active_color,
                    font=self.font,
                    font_size=self.font_size,
                    size=(char_width + 10, max_height + int(self.font_size * 0.5)),
                    transparent=True,
                )
                clip.mask = clip.mask.with_effects([vfx.FadeIn(0.2)])
                clip = clip.with_start(word.start + i * char_duration)
                clip = clip.with_duration(char_duration)
                clip = clip.with_duration(phrase.end - (word.start + i * char_duration))
                clip = clip.with_position((current_pos, 0))
                word_char_clips.append(clip)

                current_pos += char_width
            temp_clip = TextClip(text=" ", font_size=self.font_size, font=self.font)
            current_pos += temp_clip.w
            char_clips.extend(word_char_clips)

        bg_rect = ColorClip((current_pos, adjusted_height), color=self.back_color, duration=phrase.end - phrase.start)
        bg_rect = bg_rect.with_start(phrase.start)
        return CompositeVideoClip([bg_rect] + char_clips, size=(current_pos, adjusted_height))

    def get_text_dimensions(self, text):
        clip = TextClip(text=text, font_size=self.font_size, font=self.font)
        return clip.w, clip.h

    def compile_video(
            self,
            song_title: str,
            cover_image: ImagePath,
            back_track: AudioPath,
            timestamped_phrases: list[Phrase],
            destination: Path | None = None,
    ) -> VideoPath:

        # Загрузка и проверка аудио
        audio_clip = AudioFileClip(back_track)
        total_duration = audio_clip.duration

        # Загружаем фоновое изображение
        background = self.create_background_with_image(cover_image, self.output_size).with_duration(total_duration)

        clips = []
        # Вычисляем высоту строки с запасом
        line_height = self.get_text_dimensions(timestamped_phrases[0].text)[1] + int(
            self.font_size * 0.5) + 10

        previous_phrase = None
        # Верхняя линия: анимированные клипы для каждой фразы
        for phrase in timestamped_phrases:
            phrase.start = previous_phrase.end if previous_phrase is not None else 0.0
            animated_clip = self.create_phrase_animation(phrase).with_position(('center', 0))
            clips.append(animated_clip)
            previous_phrase = phrase

        # Нижняя линия: статические клипы для следующих фраз
        if len(timestamped_phrases) > 1:
            # Начальный статический клип для второй фразы с 0 до её start
            static_bottom_initial = self.create_static_phrase_clip(timestamped_phrases[1],
                                                                   timestamped_phrases[1].start).with_position(
                ('center', line_height))
            clips.append(static_bottom_initial)

            # Статические клипы для всех последующих фраз
            for i in range(1, len(timestamped_phrases) - 1):
                next_phrase = timestamped_phrases[i + 1]
                start_time = timestamped_phrases[i].start
                end_time = next_phrase.start
                duration = end_time - start_time
                if duration > 0:
                    static_bottom = self.create_static_phrase_clip(next_phrase, duration).with_position(
                        ('center', line_height)).with_start(start_time)
                    clips.append(static_bottom)

        # Определяем размеры композиции фраз
        max_width = max(
            self.get_text_dimensions(phrase.text)[0] for phrase in timestamped_phrases)
        total_height = 2 * line_height

        # Создаем композицию фраз
        phrase_composite = CompositeVideoClip(clips, size=(max_width, total_height)).with_duration(total_duration)

        # Центрируем композицию фраз в кадре 1920x1080
        pos_x = (self.output_size[0] - max_width) / 2
        pos_y = (self.output_size[1] - total_height) / 2
        phrase_composite = phrase_composite.with_position((pos_x, pos_y))

        # Создаем финальный клип с фоном и фразами
        final_clip = CompositeVideoClip([background, phrase_composite], size=self.output_size)
        final_clip = final_clip.with_audio(audio_clip)

        # Экспорт
        output_path = destination or Path(f"{song_title}_karaoke.mp4")
        final_clip.write_videofile(
            filename=output_path,
            fps=self.fps,
            codec='libx264',
            audio_codec='aac',
            threads=12,
            preset='ultrafast',
            # ffmpeg_params=['-crf', '18']
        )

        return VideoPath(output_path)


if __name__ == '__main__':
    song_title = "Cage the elephant - Come a little closer"
    # song_title = "Imagine Dragons - Bones"
    # song_title = "Wengie & i-dle - EMPIRE (English Version)"
    # song_title = "Немного нервно - Пожар"

    media_folder = Path("media")
    song_folder = media_folder / song_title
    back_track = song_folder / "accompaniment.wav"
    with open(song_folder / "linking.json") as file:
        json_file = json.load(file)
        phrases = adaptix.load(json_file, list[Phrase])

    video_maker = FfmpegVideoMaker()

    video = video_maker.compile_video(
        song_title=song_title,
        cover_image=next(song_folder.glob("cover.*")),
        back_track=back_track,
        timestamped_phrases=phrases,
        destination=song_folder / "karaoke.mp4",
    )
