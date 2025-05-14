import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from core.application.text_generation import TextGenerator


class GeniusTextScrapper(TextGenerator):
    def get_text_for_a_song(self, song_title: str) -> str:
        base_url = "https://api.genius.com"
        token = os.getenv("GENIUS_TOKEN")
        auth_header = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{base_url}/search?q={song_title}", headers=auth_header)
        result = response.json()
        assert result["meta"]["status"] == 200, result
        hits = result["response"]["hits"]
        songs = [
            api_object
            for api_object in hits
            if api_object["type"] == "song"
        ]
        first_matched_song = songs[0]
        page_response = requests.get(f"{first_matched_song['result']['url']}", headers=auth_header)
        html = BeautifulSoup(page_response.text.replace('<br/>', '\n'), "html.parser")
        # Determine the class of the div
        divs = html.find_all("div", attrs={'data-lyrics-container' : True})
        if divs is None or len(divs) <= 0:
            raise Exception("Couldn't find the lyrics section")

        for div in divs:
            element_to_exclude = div.find('div', attrs={"data-exclude-from-selection": "true"})
            if element_to_exclude is not None:
                element_to_exclude.decompose()

        lyrics = "\n".join([div.get_text() for div in divs])

        # Remove [Verse], [Bridge], etc.
        # if self.remove_section_headers or remove_section_headers:
        lyrics = re.sub(r'(\[.*?\])*', '', lyrics)
        lyrics = re.sub('\n{2}', '\n', lyrics)  # Gaps between verses
        lyrics = re.sub('\d+ Contributors', '', lyrics)
        lyrics = re.sub('.+ Lyrics', '', lyrics)

        while '\n\n' in lyrics:
            lyrics = lyrics.replace('\n\n', '\n')

        return lyrics.strip("\n")


if __name__ == '__main__':
    song_title = "Cage the elephant - Come a little closer"
    song_text = GeniusTextScrapper().get_text_for_a_song(song_title)
    media_folder = Path("media")
    song_folder = media_folder / song_title
    print(song_text)
    with open(song_folder / "original_text.txt", mode='w', encoding='utf8') as file:
        file.write(song_text)
        print(f"Written into {file.name}")
