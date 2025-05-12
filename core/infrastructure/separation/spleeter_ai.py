from pathlib import Path

from spleeter.audio import Codec
from spleeter.audio.adapter import AudioAdapter
from spleeter.separator import Separator

from core.application.separation import AudioSeparator, SeparationResult
from core.application.dto import AudioPath


class SpleeterSeparator(AudioSeparator):
    def separate_into_vocals_and_music(self, audio_file: AudioPath, destination_folder: Path | None = None) -> SeparationResult:
        if destination_folder is None:
            destination_folder = Path("output")
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
            str(destination_folder or Path("output")),
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
                filename=destination_folder / audio_file.stem, instrument="vocals", codec=codec.value
            )),
            back_track=Path(filename_format.format(
                filename=destination_folder / audio_file.stem, instrument="accompaniment", codec=codec.value
            )),
        )


if __name__ == "__main__":
    song_title = "Cage the elephant - Come a little closer"
    media_folder = Path("media")
    song_folder = media_folder / song_title
    input_audio_file = song_folder / "audio.mp3"
    print(SpleeterSeparator().separate_into_vocals_and_music(input_audio_file))
