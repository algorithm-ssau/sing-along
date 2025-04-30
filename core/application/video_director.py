from core.application.separation import AudioSeparator
from core.application.text_generation import TextGenerator
from core.application.timestamp_linking import TimestampLinker
from core.application.video_maker import VideoMaker
from core.application.dto import AudioPath, ImagePath, VideoPath
from core.application.voice_recognition import VoiceRecognizer, Phrase


class VideoDirector:
    def __init__(
            self,
            audio_separator: AudioSeparator,
            text_generator: TextGenerator,
            voice_recognizer: VoiceRecognizer,
            timestamp_linker: TimestampLinker,
            video_maker: VideoMaker,
    ):
        self._audio_separator = audio_separator
        self._text_generator = text_generator
        self._voice_recognizer = voice_recognizer
        self._timestamp_linker = timestamp_linker
        self._video_maker = video_maker

    def make_video(self, audio: AudioPath, song_title: str, cover_image: ImagePath) -> VideoPath:
        separation_result = self._audio_separator.separate_into_vocals_and_music(audio_file=audio)
        recognized_phrases = self._voice_recognizer.get_text_from_vocals(vocals=separation_result.vocals)
        song_text = self._text_generator.get_text_for_a_song(song_title=song_title)
        timestamped_phrases = self._timestamp_linker.link_timestamps_to_song_text(full_text=song_text,
                                                                                  phrases=recognized_phrases)
        return self._video_maker.compile_video(song_title=song_title, cover_image=cover_image,
                                               back_track=separation_result.back_track,
                                               timestamped_phrases=timestamped_phrases)
