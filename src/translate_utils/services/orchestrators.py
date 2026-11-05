import concurrent.futures
from pathlib import Path

from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.progress import (
    Progress as RichProgress,
)

from translate_utils.core.entities import (
    FileProgressSummary,
    LanguageCheckResults,
    Progress,
    TranslationStats,
)
from translate_utils.infrastructure.logger import get_logger
from translate_utils.infrastructure.types import ExecutorFactory
from translate_utils.services.language_check_service import LanguageCheckService
from translate_utils.services.progress_service import ProgressService

LOGGER = get_logger(__name__)


class BatchProgressOrchestrator:
    """
    Orchestrates the batch processing of multiple translation files.
    Hides concurrency and data aggregation mechanics from the presentation layer.
    """

    def __init__(
        self, progress_service: ProgressService, executor_factory: ExecutorFactory | None = None
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

        sorted_file_details = dict(sorted(file_details.items()))
        sorted_failed_files = dict(sorted(failed_files.items()))

        return TranslationStats(
            file_details=sorted_file_details,
            global_total=global_total,
            failed_files=sorted_failed_files,
        )


class BatchLanguageCheckOrchestrator:
    def __init__(
        self,
        service: LanguageCheckService,
        executor_factory: ExecutorFactory | None = None,
    ) -> None:
        self.service = service
        self.executor_factory = executor_factory or concurrent.futures.ThreadPoolExecutor

    def execute(self, files: list[Path]) -> LanguageCheckResults:
        results = LanguageCheckResults()

        with RichProgress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            refresh_per_second=10,
        ) as progress:
            overall_task = progress.add_task("[bold green]Overall Files", total=len(files))

            with self.executor_factory() as executor:
                future_to_file = {
                    executor.submit(self.service.check_file, file_path, progress): file_path
                    for file_path in files
                }

                for future in concurrent.futures.as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        file_result = future.result()
                        results.file_results.append(file_result)
                    except Exception as exc:
                        results.failed_files[str(file_path)] = str(exc)
                    finally:
                        progress.advance(overall_task)

        return results
