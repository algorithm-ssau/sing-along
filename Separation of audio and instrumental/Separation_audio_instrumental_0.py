from spleeter.separator import Separator


def separate_audio(input_file: str, output_path: str):
    """
    Разделяет аудиофайл на вокал и инструментал.

    :param input_file: Путь к входному аудиофайлу.
    :param output_path: Директория для сохранения результатов.
    """
    # Инициализация модели (2stems — разделение на вокал и инструментал)
    separator = Separator('spleeter:2stems')

    # Разделение аудио
    separator.separate_to_file(input_file, output_path)


# Пример использования
separate_audio('song.mp3', 'output')
