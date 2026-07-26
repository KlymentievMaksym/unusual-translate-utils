from pathlib import Path

from translate_utils.core.entities import FileStats
from translate_utils.core.interfaces import ProgressCounterFunc, ReadStrategy
from translate_utils.infrastructure.logger import get_logger

LOGGER = get_logger(__name__)


class ProgressService:
    def __init__(
            self,
            file_reader: ReadStrategy,
            progress_counter: ProgressCounterFunc
        ) -> None:

        self._file_reader = file_reader
        self._progress_counter = progress_counter

    def process_single_file(self, filepath: Path) -> FileStats | None:
        file_text = self._file_reader(filepath)
        summary = self._progress_counter(file_text)

        if not summary.is_empty:
            return FileStats(filepath.name, summary)

        return None
