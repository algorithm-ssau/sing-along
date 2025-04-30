from dataclasses import dataclass
from typing import Protocol

from core.application.dto import AudioPath


@dataclass(slots=True, frozen=True)
class SeparationResult:
    vocals: AudioPath
    back_track: AudioPath


class AudioSeparator(Protocol):
    def separate_into_vocals_and_music(self, audio_file: AudioPath) -> SeparationResult:
        ...
