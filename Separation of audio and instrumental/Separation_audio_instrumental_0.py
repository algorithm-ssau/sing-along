from spleeter.separator import Separator
import os
import glob


def separate_audio_batch(input_folder: str, output_folder: str):
    """
    Разделяет аудиофайл на вокал и инструменталс с созданием выходной папки при необходимости.


    :param input_file: Путь к входному аудиофайлу.
    :param output_path: Директория для сохранения результатов.
    """
    supported_formats = ['*.mp3', '*.wav', '*.flac', '*.ogg', '*.m4a']
    audio_files = []

    for file_format in supported_formats:
        audio_files.extend(glob.glob(os.path.join(input_folder, file_format)))

    if not audio_files:
        print(f"Ошибка: В папке '{input_folder}' нет аудиофайлов.")
        return

    os.makedirs(output_folder, exist_ok=True)

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
