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
from translate_utils.infrastructure.logging.logger import get_logger

LOGGER = get_logger(__name__)


class CleanupService:
    def __init__(
        self,
        file_reader: ReadStrategy[str],
        file_parser: ParseStrategy[dict[str, DialogueLine]],
        file_cleaner: TranslationCleaner,
        file_writer: WriteStrategy[str],
        mapper: ReverseLookupMapper,
        verbose: bool = True,
    ) -> None:

        self._file_reader = file_reader
        self._file_parser = file_parser
        self._file_cleaner = file_cleaner
        self._file_writer = file_writer
        self._mapper = mapper
        self._verbose = verbose

    def clean(self, filepath: str | Path, clean_method: CleanStrategy) -> CleanResults:
        file_text = self._file_reader(filepath)

        dialogues = self._file_parser(file_text)
        if self._verbose:
            LOGGER.info(f"Parsed dict length is {len(dialogues)}")

        text_to_position = self._mapper(dialogues)

        clean_results = self._file_cleaner.clean(file_text, text_to_position, clean_method)
        if self._verbose:
            LOGGER.info(f"Replaced {clean_results.replaced_count} duplicate strings.")

        return clean_results

    def save(self, new_filepath: str | Path, clean_results: CleanResults) -> None:
        new_filepath = Path(new_filepath)

        if new_filepath.exists():
            LOGGER.warning(f"Filepath {new_filepath.absolute()} already exists, overwriting...")

        self._file_writer(
            filepath=new_filepath,
            content=clean_results.cleaned_text,
        )
        if self._verbose:
            LOGGER.info(f"Saved cleaned file to: {new_filepath}")

    def clean_and_save(
        self, filepath: str | Path, clean_method: CleanStrategy, new_name: str | Path | None = None
    ) -> CleanResults:

        clean_results = self.clean(filepath=filepath, clean_method=clean_method)

        self.save(
            new_filepath=Path(filepath) if new_name is None else Path(new_name),
            clean_results=clean_results,
        )

        return clean_results
