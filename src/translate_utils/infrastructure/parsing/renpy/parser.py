from translate_utils.core.entities import DialogueLine, TranslationsDicts
from translate_utils.core.interfaces import ParseStrategy
from translate_utils.infrastructure.parsing.renpy.regexes import (
    DLG_HASH,
    DLG_LABEL,
    RegexBlockConfig,
)


class BaseRegexParser:
    """
    Base class for regex-based parsers to share initialization logic.
    """

    def __init__(self, config: RegexBlockConfig) -> None:
        self._config = config


class RegexDialogueParser(BaseRegexParser):
    """
    Implementation of ParseStrategy[dict[str, DialogueLine]].
    """

    def __call__(self, file_text: str) -> dict[str, DialogueLine]:
        dialogues: dict[str, DialogueLine] = {}
        last_pos = 0
        last_line = 1

        for match in self._config.pattern.finditer(file_text):
            start_pos = match.start()
            end_pos = max(start_pos, match.end() - 1)
            start_line = last_line + file_text.count("\n", last_pos, start_pos)
            end_line = start_line + file_text.count("\n", start_pos, end_pos)
            last_pos = end_pos
            last_line = end_line

            data = match.groupdict()
            unique_key = f"{data[DLG_LABEL]}_{data[DLG_HASH]}"
            dialogues[unique_key] = DialogueLine(
                **data,
                start_line=start_line,
                end_line=end_line,
            )

        return dialogues


class RegexStringParser(BaseRegexParser):
    """
    Implementation of ParseStrategy[dict[str, str]].
    """

    def parse_with_lines(self, file_text: str) -> tuple[dict[str, str], dict[str, tuple[int, int]]]:
        ui_strings: dict[str, str] = {}
        string_lines: dict[str, tuple[int, int]] = {}
        last_pos = 0
        last_line = 1

        for match in self._config.pattern.finditer(file_text):
            start_pos = match.start()
            end_pos = max(start_pos, match.end() - 1)
            start_line = last_line + file_text.count("\n", last_pos, start_pos)
            end_line = start_line + file_text.count("\n", start_pos, end_pos)
            last_pos = end_pos
            last_line = end_line

            old = match.group(self._config.original_group)
            new = match.group(self._config.translated_group)
            ui_strings[old] = new
            string_lines[old] = (start_line, end_line)

        return ui_strings, string_lines

    def __call__(self, file_text: str) -> dict[str, str]:
        ui_strings, _ = self.parse_with_lines(file_text)
        return ui_strings


class RegexDialAndStrParser:
    """
    Implementation of ParseStrategy[TranslationsDicts].
    """

    def __init__(
        self,
        dialogue_parser: ParseStrategy[dict[str, DialogueLine]],
        string_parser: ParseStrategy[dict[str, str]],
    ) -> None:

        self._dialogue_parser = dialogue_parser
        self._string_parser = string_parser

    def __call__(self, file_text: str) -> TranslationsDicts:
        dialogues: dict[str, DialogueLine] = self._dialogue_parser(file_text=file_text)
        if isinstance(self._string_parser, RegexStringParser):
            ui_strings, string_lines = self._string_parser.parse_with_lines(file_text)
        else:
            ui_strings = self._string_parser(file_text=file_text)
            string_lines = {}
        return TranslationsDicts(dialogues, ui_strings, string_lines)
