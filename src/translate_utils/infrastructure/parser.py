from pathlib import Path

from translate_utils.core.regexes import RE_TRANSLATE_BLOCK, RE_STRINGS_BLOCK
from translate_utils.core.entities import DialogueLine, Progress
from translate_utils.core.rules import check_is_translated

from translate_utils.infrastructure.logger import get_logger

LOGGER = get_logger(__name__)

class RpyTranslationParser:
    """Handles the parsing of Ren'Py translation files."""
    def parse_all(self, filepath: str | Path) -> tuple[dict[str, DialogueLine], dict[str, str]]:
        file_text = self.read_file(filepath)
        dialogues = self._extract_dialogues(file_text)
        ui_strings = self._extract_strings(file_text)
        return dialogues, ui_strings

    def parse_dialogues_only(self, filepath: str | Path) -> dict[str, DialogueLine]:
        file_text = self.read_file(filepath)
        return self._extract_dialogues(file_text)

    def parse_strings_only(self, filepath: str | Path) -> dict[str, str]:
        file_text = self.read_file(filepath)
        return self._extract_strings(file_text)

    def read_file(self, filepath: str | Path) -> str:
        return Path(filepath).read_text(encoding='utf-8-sig')

    def count_progress(self, filepath: str | Path):
        """Parses a single file and returns (translated_count, total_count)."""
        file_text = self.read_file(filepath)

        dialog_translated, dialog_length = self._count_progress_dialogues(file_text)
        string_translated, string_length = self._count_progress_strings(file_text)

        total = dialog_length + string_length
        translated = dialog_translated + string_translated

        return translated, total, Progress(dialog_translated, dialog_length), Progress(string_translated, string_length)

    def _count_progress_dialogues(self, text: str) -> tuple[int, int]:
        dialog_translated = 0
        dialog_length = 0

        for match in RE_TRANSLATE_BLOCK.finditer(text):
            original = match.group(4)
            trans = match.group(6)
            
            dialog_length += 1
            if check_is_translated(original, trans): dialog_translated += 1

        return dialog_translated, dialog_length

    def _count_progress_strings(self, text: str) -> tuple[int, int]:
        string_translated = 0
        string_length = 0

        for match in RE_STRINGS_BLOCK.finditer(text):
            old = match.group(3)
            new = match.group(5)
            # old = match.group(4)
            # new = match.group(6)

            string_length += 1
            if check_is_translated(old, new): string_translated += 1

        return string_translated, string_length

    def _extract_strings(self, text: str) -> dict[str, str]:
        ui_strings: dict[str, str] = {}
        for match in RE_STRINGS_BLOCK.finditer(text):
            # if match.group(1) is None:
            # ui_strings[match.group(4)] = match.group(6)
            ui_strings[match.group(3)] = match.group(5)
        return ui_strings
        
    def _extract_dialogues(self, text: str) -> dict[str, DialogueLine]:
        dialogues: dict[str, DialogueLine] = {}
        for match in RE_TRANSLATE_BLOCK.finditer(text):
            dialogues[match.group(2)] = DialogueLine(
                script_pos=match.group(1),
                character=match.group(3),
                original=match.group(4),
                translated=match.group(6)
            )
        return dialogues