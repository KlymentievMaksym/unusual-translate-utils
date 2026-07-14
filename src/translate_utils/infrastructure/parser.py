from pathlib import Path

from translate_utils.core.regexes import RE_TRANSLATE_BLOCK, RE_STRINGS_BLOCK
from translate_utils.core.entities import DialogueLine
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

    def _extract_strings(self, text: str) -> dict[str, str]:
        ui_strings: dict[str, str] = {}
        for match in RE_STRINGS_BLOCK.finditer(text):
            # if match.group(1) is None:
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