from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from string import punctuation

from core.application.exceptions import RecognitionError
from core.application.timestamp_linking import TimestampLinker
from core.application.voice_recognition import Phrase, Word


def is_intersecting(a1, a2, b1, b2) -> bool:
    return (
            a1 <= b1 <= a2
            or a1 <= b2 <= a2
            or b1 <= a1 <= b2
            or b1 <= a2 <= b2
    )


@dataclass
class TextStorage:
    full_text: str
    phrases: list[Phrase] = field(default_factory=list)

    def __post_init__(self):
        self.phrases = [Phrase(line, float('inf'), -1, [Word(word, float('inf'), -1) for word in line.split()])
                        for line in self.full_text.splitlines()]

    def get_word_by_index(self, index):
        prev_end_i = -1
        for phrase in self.phrases:
            for word in phrase.words:
                start_i, end_i = prev_end_i + 1, prev_end_i + 1 + len(word.word)
                if start_i <= index <= end_i:
                    return word
                prev_end_i = end_i

    def write_timecode(self, start_time, end_time, start_i, end_i):
        average_index = (start_i + end_i) / 2
        word = self.get_word_by_index(average_index)
        if not word:
            return False

        word.start = min(start_time, word.start)
        word.end = max(end_time, word.end)

        return True


class TextAlignmentLinker(TimestampLinker):
    en_vowels = "aeiouу"
    ru_vowels = "еыаоэяию"
    vowels = en_vowels + ru_vowels

    ENABLE_MATCH_WORDS_LINKING = True
    ENABLE_VOWELS_LINKING = False
    MIN_VOWELS_FOR_MATCH = 2

    def __init__(self):
        self.min_full_text_ratio = 0.1
        self.min_word_ratio = 0.6

    def link_timestamps_to_song_text(self, full_text: str, phrases: list[Phrase]) -> list[Phrase]:
        recognized = "^".join(["^".join(w.word.lower() for w in p.words) for p in phrases])
        matcher = SequenceMatcher(None, full_text.lower(), recognized, autojunk=False)
        matches = matcher.get_matching_blocks()

        ratio = matcher.ratio()

        print(f'{ratio=}')

        if ratio < self.min_full_text_ratio:
            raise RecognitionError

        storage = TextStorage(full_text=full_text)
        prev_end_i = -1

        for phrase in phrases:
            for word in phrase.words:
                start_i, end_i = prev_end_i + 1, prev_end_i + 1 + len(word.word)
                prev_end_i = end_i
                assert word.word.lower() == recognized[start_i:end_i], (word.word, recognized[start_i:end_i])
                phrase_matches = [match for match in matches if
                                  is_intersecting(start_i, end_i, match.b, match.b + match.size) and
                                  not full_text[match.a:match.a + match.size].isspace()]
                has_full_match = False
                if not phrase_matches:
                    # print('Нет совпадений', word.word)
                    continue
                for block in phrase_matches:
                    if self.normalize_word(full_text[block.a:block.a + block.size]) == self.normalize_word(word.word):
                        has_full_match = True
                        storage.write_timecode(word.start, word.end, block.a, block.a + block.size)

                if has_full_match:
                    continue

                block = phrase_matches[0]
                original_word = storage.get_word_by_index((block.a * 2 + block.size) / 2)
                word_matcher = SequenceMatcher(None, self.normalize_word(original_word.word), self.normalize_word(word.word), autojunk=False)
                if self.ENABLE_MATCH_WORDS_LINKING and word_matcher.ratio() >= self.min_word_ratio:
                    storage.write_timecode(word.start, word.end, block.a, block.a + block.size)
                    # print(original_word.word, word.word, word_matcher.ratio())
                    continue

                if (self.ENABLE_VOWELS_LINKING
                        and self.vowels_count(word.word) == self.vowels_count(original_word.word)
                        and self.vowels_count(word.word) >= self.MIN_VOWELS_FOR_MATCH):
                    storage.write_timecode(word.start, word.end, block.a, block.a + block.size)
                    # print(original_word.word, word.word)

        #  Отсутствие таймкода начала или конца

        last_matched_word = Word('', start=phrases[0].start, end=phrases[0].start)
        unknown_words = []
        for phrase in storage.phrases:
            for word in phrase.words:
                if word.end != -1:
                    if unknown_words:
                        words_weight = [max(self.vowels_count(word.word), 1) for word in unknown_words]
                        start = last_matched_word.end
                        end = word.start
                        time_delta = end - start
                        total_weight = sum(words_weight)
                        var = start
                        for unknown_word, weight in zip(unknown_words, words_weight):
                            unknown_word.start = var
                            var += time_delta * weight / total_weight
                            unknown_word.end = var
                        unknown_words.clear()
                    last_matched_word = word
                else:
                    unknown_words.append(word)

        if unknown_words:
            word = Word('', start=unknown_words[-1].end, end=unknown_words[-1].end)
            words_weight = [max(self.vowels_count(word.word), 1) for word in unknown_words]
            start = last_matched_word.end
            end = word.start
            time_delta = end - start
            total_weight = sum(words_weight)
            var = start
            for unknown_word, weight in zip(unknown_words, words_weight):
                unknown_word.start = var
                var += time_delta * weight / total_weight
                unknown_word.end = var

        for phrase in storage.phrases:
            phrase.start = phrase.words[0].start
            phrase.end = phrase.words[-1].end

        return storage.phrases

    def vowels_count(self, word: str) -> int:
        return sum(map(lambda x: x in self.vowels, word))

    def normalize_word(self, word: str) -> str:
        word_strip = punctuation + ' '
        return word.lower().strip(word_strip)


if __name__ == '__main__':
    from core.infrastructure.voice_recognition.whisper_ai import WhisperRecognizer, from_json, save_to_json
    from core.infrastructure.text_generation.genius import GeniusTextScrapper

    media_folder = Path("output/Cage_The_Elephant_Come_A_Little_Closer")
    audio_filename = "vocals.wav"
    input_audio_file = media_folder / audio_filename
    # whisper_recognition = WhisperRecognizer().get_text_from_vocals(input_audio_file)
    whisper_recognition = from_json("come_a_little_closer_transrib.json")
    # print("\n".join([" ".join(w.word.lower() for w in p.words) for p in whisper_recognition]))
    # pprint(whisper_recognition)
    # song_text = GeniusTextScrapper().get_text_for_a_song("Cage the elephant - Come a little closer")
    with open("come_a_little_closer_text.txt") as f:
        song_text = f.read()

    phrases = TextAlignmentLinker().link_timestamps_to_song_text(song_text, whisper_recognition)
    save_to_json(phrases, "come_a_little_closer_linking.json")
