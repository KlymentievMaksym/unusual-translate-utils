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

        for match in self._config.pattern.finditer(file_text):
            data = match.groupdict()
            unique_key = f"{data[DLG_LABEL]}_{data[DLG_HASH]}"
            dialogues[unique_key] = DialogueLine(**data)

        return dialogues


class RegexStringParser(BaseRegexParser):
    """
    Implementation of ParseStrategy[dict[str, str]].
    """

    def __call__(self, file_text: str) -> dict[str, str]:
        ui_strings: dict[str, str] = {}

        for match in self._config.pattern.finditer(file_text):
            old = match.group(self._config.original_group)
            new = match.group(self._config.translated_group)
            ui_strings[old] = new

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
        ui_strings: dict[str, str] = self._string_parser(file_text=file_text)
        return TranslationsDicts(dialogues, ui_strings)
