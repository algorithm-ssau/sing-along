from typing import Protocol

from core.application.dto import AudioPath, ImagePath, VideoPath
from core.application.voice_recognition import Phrase


class VideoMaker(Protocol):
    def compile_video(
            self,
            song_title: str,
            cover_image: ImagePath,
            back_track: AudioPath,
            timestamped_phrases: list[Phrase]
    ) -> VideoPath:
        ...
