import concurrent.futures
from pathlib import Path

from translate_utils.core.entities import FileProgressSummary, Progress, TranslationStats
from translate_utils.infrastructure.logger import get_logger
from translate_utils.infrastructure.types import ExecutorFactory
from translate_utils.services.progress_service import ProgressService

LOGGER = get_logger(__name__)


class BatchProgressOrchestrator:
    """
    Orchestrates the batch processing of multiple translation files.
    Hides concurrency and data aggregation mechanics from the presentation layer.
    """
    def __init__(
            self,
            progress_service: ProgressService,
            executor_factory: ExecutorFactory | None = None
        ) -> None:

        self._progress_service = progress_service
        self._executor_factory = executor_factory or concurrent.futures.ThreadPoolExecutor

    def execute(self, rpy_files: list[Path]) -> TranslationStats:
        if not rpy_files:
            return TranslationStats()

        file_details: dict[str, FileProgressSummary] = {}
        failed_files: dict[str, str] = {}
        global_total = Progress()

        with self._executor_factory() as executor:
            future_to_file = {
                executor.submit(self._progress_service.process_single_file, filepath): filepath
                for filepath in rpy_files
            }
            for future in concurrent.futures.as_completed(future_to_file):
                filepath = future_to_file[future]
                try:
                    result = future.result()
                    if result is not None:
                        file_details[result.name] = result.summary
                        global_total += result.summary.total
                except Exception as e:
                    LOGGER.error(f"Worker failed on {filepath.name}", exc_info=True)
                    failed_files[filepath.name] = str(e)

        return TranslationStats(
            file_details=file_details,
            global_total=global_total,
            failed_files=failed_files
        )
