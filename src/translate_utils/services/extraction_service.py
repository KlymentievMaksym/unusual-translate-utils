from pathlib import Path

from translate_utils.core.entities import FileReaderFunc, TranslationsDicts
from translate_utils.infrastructure.parser import ParseStrategy


class ExtractionService:
    def __init__(self, file_parser: ParseStrategy, file_reader: FileReaderFunc) -> None:
        self._file_parser = file_parser
        self._file_reader = file_reader

    def get_translation_dicts(self, filepath: str | Path) -> TranslationsDicts:
        file_text = self._file_reader(filepath)
        return self._file_parser(file_text)
