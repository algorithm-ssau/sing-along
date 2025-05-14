import json
import math
from difflib import SequenceMatcher
from pathlib import Path

import adaptix

from core.application.timestamp_linking import TimestampLinker
from core.application.voice_recognition import Phrase, Word
from core.infrastructure.timestamp_linking.text_alignment_linking import TextAlignmentLinker
from core.infrastructure.voice_recognition.whisper_ai import save_to_json


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def visualize_diff(matcher, a, b):
    result = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            result.append(a[i1:i2])
        elif tag == 'replace':
            result.append(f"{bcolors.RED}{a[i1:i2]}{bcolors.ENDC}{bcolors.GREEN}{b[j1:j2]}{bcolors.ENDC}")
        elif tag == 'delete':
            result.append(f"{bcolors.RED}{a[i1:i2]}{bcolors.ENDC}")
        elif tag == 'insert':
            result.append(f"{bcolors.GREEN}{b[j1:j2]}{bcolors.ENDC}")
    return ''.join(result)


class WordGrabberTextAlignmentLinker(TimestampLinker):
    MAX_PHRASES_TO_SKIP = 6
    MAX_TOLERANCE = 0.6
    MAX_WORDS_PER_LINE = 50

    en_vowels = "aeiouу"
    ru_vowels = "еыаоэяию"
    vowels = en_vowels + ru_vowels

    def vowels_count(self, word: str) -> int:
        return sum(map(lambda x: x in self.vowels, word))

    def match_words_timestamps(self, line: str, phrases: list[Phrase]) -> Phrase:
        linker = TextAlignmentLinker()
        phrase = linker.link_timestamps_to_song_text(line, phrases)[0]
        phrase.start = phrases[0].start
        phrase.words[0].start = phrases[0].start
        phrase.end = phrases[-1].end
        phrase.words[-1].end = phrases[-1].end
        return phrase

    def gen_empty_phrase(self, line: str) -> Phrase:
        return Phrase(line, math.inf, -1, [Word(word, math.inf, -1) for word in line.split()])

    def split_time_by_phrases(self, phrases: list[Phrase], start: float, end: float):
        phrases_weight = [sum([max(self.vowels_count(word.word), 1) for word in phrase.words]) for phrase in phrases]
        total_weight = sum(phrases_weight)
        time_delta = end - start
        var = start
        for unknown_phrase, weight in zip(phrases, phrases_weight):
            unknown_phrase.start = var
            var += time_delta * weight / total_weight
            unknown_phrase.end = var
            self.fill_timestamp_spaces(unknown_phrase)

    def fill_timestamp_spaces(self, phrase: Phrase):
        assert phrase.start != math.inf and phrase.end != -1, phrase
        words_weight = [max(self.vowels_count(word.word), 1) for word in phrase.words]
        start = phrase.start
        end = phrase.end
        time_delta = end - start
        total_weight = sum(words_weight)
        var = start
        for unknown_word, weight in zip(phrase.words, words_weight):
            unknown_word.start = var
            var += time_delta * weight / total_weight
            unknown_word.end = var

    def link_timestamps_to_song_text(self, full_text: str, phrases: list[Phrase]) -> list[Phrase]:
        missing = 0
        found = 0

        result = []

        words = sum([phrase.words for phrase in phrases], start=[])
        first_unreclaimed_word = 0
        for full_text_line in full_text.split('\n'):
            for max_words_to_skip in range(5, 55):
                ratios = dict()
                # print(words[first_unreclaimed_word])
                for words_to_skip in range(max_words_to_skip):
                    for words_to_take in range(self.MAX_WORDS_PER_LINE):
                        if first_unreclaimed_word + words_to_skip + words_to_take >= len(words):
                            continue
                        current_words = words[
                                        first_unreclaimed_word + words_to_skip:first_unreclaimed_word + words_to_skip + words_to_take
                                        ]
                        current_text = " ".join([word.word.strip() for word in current_words])
                        matcher = SequenceMatcher(None, full_text_line, current_text)
                        ratio = matcher.ratio()
                        if ratio not in ratios:
                            ratios[ratio] = (words_to_skip, words_to_take, current_text, current_words)
                        else:
                            old_ratio = ratios[ratio]
                            if words_to_skip < old_ratio[0]:
                                ratios[ratio] = (words_to_skip, words_to_take, current_text)
                best_ratio = max(ratios)
                best = ratios[best_ratio]
                words_to_skip, words_to_take, current_text, current_words = best
                if best_ratio > self.MAX_TOLERANCE:
                    print(f"{bcolors.OKBLUE}{full_text_line} | {current_text} | { best_ratio=} {words_to_skip=} {words_to_take=}{bcolors.ENDC}")
                    first_unreclaimed_word += words_to_skip + words_to_take
                    found += 1
                    result.append(self.match_words_timestamps(full_text_line, [Phrase(text=current_text, start=current_words[0].start, end=current_words[-1].end, words=current_words)]))
                    break
            else:
                result.append(self.gen_empty_phrase(full_text_line))
                print(f"{bcolors.RED}{full_text_line}{bcolors.ENDC}")
                missing += 1
        print(f"{missing=} {found=} {first_unreclaimed_word=} {len(words)=}")

        unknown_phrases = []
        last_known_phrase = phrases[0]
        for i, phrase in enumerate(result):
            if phrase.start == math.inf and phrase.end == -1:
                unknown_phrases.append(phrase)
            else:
                if unknown_phrases:
                    self.split_time_by_phrases(unknown_phrases, last_known_phrase.end, phrase.start)
                    unknown_phrases.clear()
                last_known_phrase = phrase

        return result


if __name__ == '__main__':

    # song_title = "Cage the elephant - Come a little closer"  # missing=6 found=33  # {5: 13, 6: 13, 7: 13, 8: 13, 9: 13, 10: 14, 11: 14, 12: 14, 13: 14, 14: 14}
    # song_title = "Imagine Dragons - Bones"  # missing=2 found=47  # {8: 3, 9: 3, 10: 3, 11: 4, 12: 4, 13: 4, 14: 5, 5: 21, 6: 21, 7: 21}
    # song_title = "Aespa - Whiplash"  # missing=32 found=33  # {14: 34, 12: 38, 13: 38, 11: 57, 5: 63, 6: 63, 7: 63, 8: 63, 9: 63, 10: 63}
    # song_title = "Wengie & i-dle - EMPIRE (English Version)"  # missing=3 found=49  # {13: 3, 14: 3, 5: 21, 6: 21, 7: 21, 8: 21, 9: 21, 10: 21, 11: 21, 12: 21}
    song_title = "Немного нервно - Пожар"  # missing=2 found=40  # {5: 2, 6: 2, 7: 2, 8: 2, 9: 2, 10: 2, 11: 2, 12: 2, 13: 2, 14: 2}
    media_folder = Path("media")
    song_folder = media_folder / song_title
    with open(song_folder / "transcribe.json") as file:
        json_file = json.load(file)
        whisper_recognition = adaptix.load(json_file, list[Phrase])
    # print("\n".join([" ".join(w.word.lower() for w in p.words) for p in whisper_recognition]))
    # pprint(whisper_recognition)
    # song_text = GeniusTextScrapper().get_text_for_a_song("Cage the elephant - Come a little closer")
    with open(song_folder / "original_text.txt") as f:
        song_text = f.read()
    phrases = WordGrabberTextAlignmentLinker().link_timestamps_to_song_text(song_text, whisper_recognition)
    save_to_json(phrases, song_folder / "linking.json")
