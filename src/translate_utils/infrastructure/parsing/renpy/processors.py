from re import Pattern

from translate_utils.infrastructure.parsing.renpy.regexes import RE_TAGS, RE_WORDS


class RenpyProcessor:
    def __init__(
        self, RE_strip_tags: Pattern[str] = RE_TAGS, RE_extract_words: Pattern[str] = RE_WORDS
    ) -> None:

        self.RE_strip_tags = RE_strip_tags
        self.RE_extract_words = RE_extract_words

    def strip_tags(self, text: str) -> str:
        return self.RE_strip_tags.sub("", text)

    def extract_words(self, text: str) -> list[str]:
        return self.RE_extract_words.findall(text)
