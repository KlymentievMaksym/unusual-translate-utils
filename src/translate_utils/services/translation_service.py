from pathlib import Path

from translate_utils.core.entities import DialogueLine, FileProgressSummary
from translate_utils.infrastructure.counter import ProgressCounter
from translate_utils.infrastructure.io import FileManager
from translate_utils.infrastructure.logger import get_logger
from translate_utils.infrastructure.parser import RpyTranslationParser

LOGGER = get_logger(__name__)

class TranslationService:
    def __init__(
            self,
            parser: RpyTranslationParser | None = None,
            counter: ProgressCounter | None = None
        ) -> None:

        self.parser = parser or RpyTranslationParser()
        self.counter = counter or ProgressCounter()

    def get_file_progress(
            self,
            filepath: str | Path
        ) -> FileProgressSummary:

        file_text = FileManager.read_renpy_file(filepath)
        progress_summary = self.counter.count_progress(file_text)
        return progress_summary

    def get_all_translations(
            self,
            filepath: str | Path
        ) -> tuple[dict[str, DialogueLine], dict[str, str]]:

        file_text = FileManager.read_renpy_file(filepath)
        dialogues, ui_strings = self.parser.parse_all(file_text)
        return dialogues, ui_strings
