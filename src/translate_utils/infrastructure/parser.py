from translate_utils.core.entities import DialogueLine
from translate_utils.core.regexes import RE_STRINGS_BLOCK, RE_TRANSLATE_BLOCK
from translate_utils.infrastructure.logger import get_logger

LOGGER = get_logger(__name__)

class RpyTranslationParser:
    """Handles the parsing of Ren'Py translation files."""
    def parse_all(self, file_text: str) -> tuple[dict[str, DialogueLine], dict[str, str]]:
        dialogues = self._extract_dialogues(file_text)
        ui_strings = self._extract_strings(file_text)
        return dialogues, ui_strings

    def parse_dialogues_only(self, file_text: str) -> dict[str, DialogueLine]:
        return self._extract_dialogues(file_text)

    def parse_strings_only(self, file_text: str) -> dict[str, str]:
        return self._extract_strings(file_text)


    @staticmethod
    def _extract_strings(text: str) -> dict[str, str]:
        ui_strings: dict[str, str] = {}
        for match in RE_STRINGS_BLOCK.finditer(text):
            old = match.group("old_text")
            new = match.group("new_text")

            # script_position = match.group("script_position")
            # if script_position is None:
            ui_strings[old] = new
        return ui_strings

    @staticmethod
    def _extract_dialogues(text: str) -> dict[str, DialogueLine]:
        dialogues: dict[str, DialogueLine] = {}
        for match in RE_TRANSLATE_BLOCK.finditer(text):
            data = match.groupdict()
            dialogues[data["script_label"]] = DialogueLine(**data)
        return dialogues
