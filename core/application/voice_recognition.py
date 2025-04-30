from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(slots=True)
class Word:
    word: str
    start: float
    end: float


@dataclass(slots=True)
class Phrase:
    text: str
    start: float
    end: float
    words: list[Word]


class VoiceRecognizer(Protocol):
    def get_text_from_vocals(self, vocals: Path) -> list[Phrase]:
        ...
