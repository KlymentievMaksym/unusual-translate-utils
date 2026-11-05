from translate_utils.core.entities import FileProgressSummary, Progress
from translate_utils.core.rules import TranslationValidator
from translate_utils.infrastructure.logging.logger import get_logger
from translate_utils.infrastructure.parsers.regexes import RegexBlockConfig

LOGGER = get_logger(__name__)


class RegexProgressCounter:
    """
    Implementation of ProgressCounterFunc.
    Counts translation progress using injected regex configurations and validator.
    """

    def __init__(
        self,
        validator: TranslationValidator,
        dialogues_config: RegexBlockConfig,
        strings_config: RegexBlockConfig,
    ) -> None:

        self._validator = validator
        self._dialogues_config = dialogues_config
        self._strings_config = strings_config

    def __call__(self, file_text: str) -> FileProgressSummary:
        dialogues = self._count_block(file_text, self._dialogues_config)
        strings = self._count_block(file_text, self._strings_config)

        progress_summary = FileProgressSummary(dialogues + strings, dialogues, strings)

        return progress_summary

    def _count_block(self, text: str, regex_config: RegexBlockConfig) -> Progress:

        translated = 0
        length = 0

        for match in regex_config.pattern.finditer(text):
            original = match.group(regex_config.original_group)
            transl = match.group(regex_config.translated_group)

            length += 1
            if self._validator.check_is_translated(original, transl):
                translated += 1

        return Progress(translated, length)
