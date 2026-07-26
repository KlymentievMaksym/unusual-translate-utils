from pathlib import Path

from translate_utils.core.cleaner import TranslationCleaner
from translate_utils.core.entities import CleanResults, DialogueLine
from translate_utils.core.interfaces import (
    CleanStrategy,
    ParseStrategy,
    ReadStrategy,
    ReverseLookupMapper,
    WriteStrategy,
)
from translate_utils.infrastructure.logger import get_logger

LOGGER = get_logger(__name__)

class CleanupService:
    def __init__(
            self,
            file_reader: ReadStrategy[str],
            file_parser: ParseStrategy[dict[str, DialogueLine]],
            file_cleaner: TranslationCleaner,
            file_writer: WriteStrategy[str],
            mapper: ReverseLookupMapper,
        ) -> None:

        self._file_reader = file_reader
        self._file_parser = file_parser
        self._file_cleaner = file_cleaner
        self._file_writer = file_writer
        self._mapper = mapper

    def clean_and_save(
            self,
            filepath: str | Path,
            clean_method: CleanStrategy,
            new_name: str | Path | None
        ) -> CleanResults:

        file_text = self._file_reader(filepath)

        new_filepath: Path = Path(filepath) if new_name is None else Path(new_name)
        if new_filepath.exists():
            LOGGER.warning(f"Filepath {new_filepath.absolute()} already exists, overwriting...")

        dialogues = self._file_parser(file_text)
        LOGGER.info(f"Parsed dict length is {len(dialogues)}")

        text_to_position = self._mapper(dialogues)

        clean_results = self._file_cleaner.clean(file_text, text_to_position, clean_method)
        LOGGER.info(f"Replaced {clean_results.replaced_count} duplicate strings.")

        self._file_writer(
            filepath=new_filepath,
            content=clean_results.cleaned_text,
        )
        LOGGER.info(f"Saved cleaned file to: {new_filepath}")

        return clean_results
