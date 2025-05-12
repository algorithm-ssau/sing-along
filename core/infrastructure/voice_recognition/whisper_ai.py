from dataclasses import dataclass

from core.application.voice_recognition import VoiceRecognizer, Phrase
from core.application.dto import AudioPath

import whisper
from adaptix import Retort


@dataclass(slots=True, frozen=True)
class Word:
    start: float
    end: float
    word: str


@dataclass(slots=True, frozen=True)
class Segment:
    text: str
    start: float
    end: float
    words: list[Word]


@dataclass(slots=True, frozen=True)
class WhisperResponse:
    segments: list[Segment]


class WhisperRecognizer(VoiceRecognizer):
    def __init__(self):
        self.retort = Retort(strict_coercion=False)
        self.model_name = "large"

    def get_text_from_vocals(self, vocals: AudioPath) -> list[Phrase]:
        model = whisper.load_model(self.model_name)
        result = model.transcribe(str(vocals), word_timestamps=True, fp16=False)

        whisper_response = self.retort.load(result, WhisperResponse)

        res = self._map_response(whisper_response)

        return res

    def _map_response(self, response: WhisperResponse) -> list[Phrase]:
        result = []
        for segment in response.segments:
            words = [word for word in segment.words if word.word != ""]
            if words:
                result.append(Phrase(segment.text.strip(), segment.start, segment.end, segment.words))
        return result
