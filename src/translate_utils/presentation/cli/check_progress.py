import concurrent.futures
from pathlib import Path

from translate_utils.infrastructure.caching.cache import CachedFileReader
from translate_utils.infrastructure.composition.factories import create_default_progress_counter
from translate_utils.infrastructure.filesystem.io import gather_extension_files, read_renpy_file
from translate_utils.infrastructure.filesystem.path import initialize_config
from translate_utils.infrastructure.filesystem.updater import update_readme_progress
from translate_utils.infrastructure.logging.logger import get_logger, setup_logging
from translate_utils.presentation.cli.args import check_translation_progress_parse_args
from translate_utils.presentation.visualize.markdown import ProgressMarkdownReport
from translate_utils.presentation.visualize.mixins import ProgressReportData
from translate_utils.presentation.visualize.terminal import ProgressTerminalReport
from translate_utils.services.orchestrators import BatchProgressOrchestrator
from translate_utils.services.progress_service import ProgressService

LOGGER = get_logger("TranslationProgress")


def check_translation_progress() -> None:
    args = check_translation_progress_parse_args()
    config = initialize_config()
    setup_logging("TranslationProgress", config.paths.common_logs_dir)
    LOGGER.info("Checking translation status...")

    if not args.filepaths:
        paths_to_check = [config.settings.dir_for_translation]
        LOGGER.info(f"No path provided. Defaulting to: {config.settings.dir_for_translation}")
    else:
        paths_to_check = [Path(p) for p in args.filepaths]

    file_reader = CachedFileReader(read_renpy_file)

    progress_counter = create_default_progress_counter()

    progress_service = ProgressService(file_reader=file_reader, progress_counter=progress_counter)
    orchestrator = BatchProgressOrchestrator(
        progress_service, lambda: concurrent.futures.ThreadPoolExecutor()
    )

    rpy_files = gather_extension_files(paths_to_check, "rpy")

    if not rpy_files:
        LOGGER.warning("No .rpy files found to process.")
    else:
        LOGGER.info(f"Found {len(rpy_files)} files. Calculating progress...")

    translation_stats = orchestrator.execute(rpy_files)

    progress_data = ProgressReportData(translation_stats)
    ProgressTerminalReport(progress_data).display()

    if translation_stats.failed_files:
        LOGGER.warning(f"Encountered errors in {len(translation_stats.failed_files)} files:")
        for file_name, error_message in translation_stats.failed_files.items():
            LOGGER.warning(f" - {file_name}: {error_message}")

    if args.update_readme is not None:
        generated_table = ProgressMarkdownReport(progress_data).generate()
        update_readme_progress(generated_table, Path(args.update_readme))

    global_progress = translation_stats.global_total
    if not global_progress.is_empty:
        LOGGER.info(
            f"GLOBAL DONE: {global_progress.percentage:>6.2f}% "
            f"({global_progress.translated} / {global_progress.total})"
        )


if __name__ == "__main__":
    check_translation_progress()
