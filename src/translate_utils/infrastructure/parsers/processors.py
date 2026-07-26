from translate_utils.infrastructure.parsers.regexes import RE_TAGS, RE_WORDS


class RenpyProcessor():
    def strip_tags(self, text: str) -> str:
        return RE_TAGS.sub("", text)

    def extract_words(self, text: str) -> list[str]:
        return RE_WORDS.findall(text)
