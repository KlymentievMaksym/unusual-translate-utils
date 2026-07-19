import concurrent.futures as cf
from pathlib import Path
from typing import Optional

from translate_utils.core.entities import FileProgressSummary, Progress, TranslationStats
from translate_utils.infrastructure.counter import ProgressCounter
from translate_utils.infrastructure.io import FileManager
from translate_utils.infrastructure.logger import get_logger

LOGGER = get_logger(__name__)

class ProgressService:
    def __init__(self, counter: Optional[ProgressCounter] = None) -> None:
        self.counter = counter or ProgressCounter()

    def _gather_rpy_files(self, paths: list[Path]) -> list[Path]:
        rpy_files = []
        for target_path in paths:
            if target_path.is_file() and target_path.suffix == ".rpy":
                rpy_files.append(target_path)
            elif target_path.is_dir():
                rpy_files.extend(target_path.rglob("*.rpy"))
        return sorted(rpy_files, key=lambda path: path.name)

    def _process_single_file(self, filepath: Path)-> tuple[str, FileProgressSummary] | None:
        try:
            file_text = FileManager.read_renpy_file(filepath)
            summary = self.counter.count_progress(file_text)
            if summary.total.total > 0:
                return filepath.name, summary
        except Exception as e:
            LOGGER.error(f"Failed to process {filepath}: {e}")
        return None

    def get_translation_stats(
            self,
            paths_to_check: list[Path]
        ) -> TranslationStats:

        rpy_files = self._gather_rpy_files(paths_to_check)

        if not rpy_files:
            LOGGER.warning("No .rpy files found to process.")
            return TranslationStats()

        LOGGER.info(f"Found {len(rpy_files)} files. Calculating progress...")


        file_details: dict[str, FileProgressSummary] = {}
        global_total = Progress()
        with cf.ThreadPoolExecutor() as executor:
            results = executor.map(self._process_single_file, rpy_files)

            for result in results:
                if result is not None:
                    file_name, summary = result
                    file_details[file_name] = summary
                    global_total += summary.total

        return TranslationStats(
            file_details=file_details,
            global_total=global_total
        )
