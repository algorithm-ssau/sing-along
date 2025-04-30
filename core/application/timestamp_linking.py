from typing import Protocol

from core.application.voice_recognition import Phrase


class TimestampLinker(Protocol):
    def link_timestamps_to_song_text(self, full_text: str, phrases: list[Phrase]) -> list[Phrase]:
        """
        Принимает полный верный текст песни и подвязывает его под распознанные слова с временными метками
        """
