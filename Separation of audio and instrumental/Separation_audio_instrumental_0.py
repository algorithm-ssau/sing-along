from spleeter.separator import Separator
import os


def separate_audio(input_file: str, output_path: str):
    """
    Разделяет аудиофайл на вокал и инструментал.

    :param input_file: Путь к входному аудиофайлу.
    :param output_path: Директория для сохранения результатов.
    """
    if not os.path.exists(input_file):
        print(f"Ошибка: Файл '{input_file}' не найден.")
        return

    try:
        separator = Separator('spleeter:2stems')
        separator.separate_to_file(input_file, output_path)
        print(f"Разделение завершено. Файлы сохранены в {output_path}")
    except Exception as e:
        print(f"Ошибка при разделении аудио: {e}")


# Пример использования
separate_audio('song.mp3', 'output')
