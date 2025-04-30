from typing import Protocol


class TextGenerator(Protocol):
    # Discussion Мб стоит возвращать list[lines] для больших гарантий структуры
    def get_text_for_a_song(self, song_title: str) -> str:
        ...
