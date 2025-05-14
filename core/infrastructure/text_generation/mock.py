from pathlib import Path

from core.application.text_generation import TextGenerator


class MockTextScrapper(TextGenerator):
    def get_text_for_a_song(self, song_title: str) -> str:
        media_folder = Path('media')
        song_folder = media_folder / 'Cage the elephant - Come a little closer'
        with open(song_folder / 'original_text.txt') as f:
            return f.read()
