from re import Pattern

from translate_utils.core.entities import FileProgressSummary, Progress
from translate_utils.core.regexes import RE_STRINGS_BLOCK, RE_TRANSLATE_BLOCK
from translate_utils.core.rules import check_is_translated
from translate_utils.infrastructure.logger import get_logger

LOGGER = get_logger(__name__)

class ProgressCounter:
    def count_progress(self, file_text: str) -> FileProgressSummary:
        """Parses a text and returns FileProgressSummary."""

        dialogues = self._count_block(
            file_text,
            RE_TRANSLATE_BLOCK,
            "original_text",
            "translation_text"
        )
        strings = self._count_block(
            file_text,
            RE_STRINGS_BLOCK,
            "old_text",
            "new_text"
        )

        progress_summary = FileProgressSummary(
            dialogues + strings,
            dialogues,
            strings
        )

        return progress_summary

    @staticmethod
    def _count_block(
        text: str,
        regex: Pattern[str],
        original_group: str,
        translated_group: str
    ) -> Progress:

        translated = 0
        length = 0

        for match in regex.finditer(text):
            original = match.group(original_group)
            transl = match.group(translated_group)

            length += 1
            if check_is_translated(original, transl):
                translated += 1

        return Progress(translated, length)
