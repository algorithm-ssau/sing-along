from pathlib import Path

from spleeter.audio import Codec
from spleeter.audio.adapter import AudioAdapter
from spleeter.separator import Separator

from core.application.separation import AudioSeparator, SeparationResult
from core.application.dto import AudioPath


class SpleeterSeparator(AudioSeparator):
    def separate_into_vocals_and_music(self, audio_file: AudioPath) -> SeparationResult:
        output_path = Path("output")  # todo
        separation_params = "spleeter:2stems"
        mwf = False
        adapter = "spleeter.audio.ffmpeg.FFMPEGProcessAudioAdapter"
        audio_adapter: AudioAdapter = AudioAdapter.get(adapter)
        offset = 0
        duration = 600.0 # todo
        bitrate = "128k" # todo
        codec = Codec.WAV
        filename_format = "{filename}/{instrument}.{codec}"
        separator = Separator(
            params_descriptor=separation_params,
            MWF=mwf,
        )
        separator.separate_to_file(
            str(audio_file),
            str(output_path),
            audio_adapter=audio_adapter,
            offset=offset,
            duration=duration,
            codec=codec,
            bitrate=bitrate,
            filename_format=filename_format,
            synchronous=False,
        )
        separator.join()
        return SeparationResult(
            vocals=Path(filename_format.format(
                filename=output_path / audio_file.stem, instrument="vocals", codec=codec.value
            )),
            back_track=Path(filename_format.format(
                filename=output_path / audio_file.stem, instrument="accompaniment", codec=codec.value
            )),
        )
