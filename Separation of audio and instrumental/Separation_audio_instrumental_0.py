from spleeter.separator import Separator
import os
import glob


def separate_audio_batch(input_folder: str, output_folder: str):
    """
    Разделяет аудиофайл на вокал и инструментал.

    :param input_file: Путь к входному аудиофайлу.
    :param output_path: Директория для сохранения результатов.
    """
    audio_files = glob.glob(os.path.join(input_folder, "*.mp3")) + glob.glob(os.path.join(input_folder, "*.wav"))

    if not audio_files:
        print(f"Ошибка: В папке '{input_folder}' нет аудиофайлов.")
        return

    separator = Separator('spleeter:2stems')

    for file in audio_files:
        try:
            print(f"Обрабатывается: {file}")
            separator.separate_to_file(file, output_folder)
            print(f"Разделение завершено для: {file}")
        except Exception as e:
            print(f"Ошибка при обработке '{file}': {e}")


# Пример использования
separate_audio_batch('input_songs', 'output')
