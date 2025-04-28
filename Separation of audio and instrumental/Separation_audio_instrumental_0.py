from spleeter.separator import Separator
import os
import glob


def separate_audio_batch(input_folder: str, output_folder: str):
    """
    Разделяет аудиофайл на вокал и инструменталс с созданием выходной папки при необходимости.
    И пропускает файлы, которые уже были обработаны. Обрабатывает ошибку загрузки модели.

    :param input_file: Путь к входному аудиофайлу.
    :param output_path: Директория для сохранения результатов.
    """
    supported_formats = ['*.mp3', '*.wav', '*.flac', '*.ogg', '*.m4a']
    audio_files = []

    for file_format in supported_formats:
        audio_files.extend(glob.glob(os.path.join(input_folder, file_format)))

    if not audio_files:
        print(f"Ошибка: В папке '{input_folder}' нет поддерживаемых аудиофайлов.")
        return

    os.makedirs(output_folder, exist_ok=True)

    try:
        separator = Separator('spleeter:2stems')
    except Exception as e:
        print(f"Ошибка при инициализации модели Spleeter: {e}")
        return

    for file in audio_files:

        file_name = os.path.splitext(os.path.basename(file))[0]
        output_song_folder = os.path.join(output_folder, file_name)

        # Проверка: если результат уже существует, пропустить файл
        if os.path.exists(os.path.join(output_song_folder, 'vocals.wav')) and \
                os.path.exists(os.path.join(output_song_folder, 'accompaniment.wav')):
            print(f"Пропущено (уже обработано): {file}")
            continue

        try:
            print(f"Обрабатывается: {file}")
            separator.separate_to_file(file, output_folder)
            print(f"Разделение завершено для: {file}")
        except Exception as e:
            print(f"Ошибка при обработке '{file}': {e}")


# Пример использования
separate_audio_batch('input_songs', 'output')
