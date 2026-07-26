import concurrent.futures
from pathlib import Path

from translate_utils.core.rules import (
    HasTargetAlphabetSpec,
    IsDifferentSpec,
    IsNotEmptySpec,
    IsSymbolOnlySpec,
    TranslationValidator,
)
from translate_utils.infrastructure.cache import CachedFileReader
from translate_utils.infrastructure.counter import RegexProgressCounter
from translate_utils.infrastructure.io import read_renpy_file
from translate_utils.infrastructure.logger import setup_logging
from translate_utils.infrastructure.parsers.processors import RenpyProcessor
from translate_utils.infrastructure.parsers.regexes import RE_STRINGS_CONFIG, RE_TRANSLATE_CONFIG
from translate_utils.infrastructure.path import DEFAULT_DIR_FOR_TRANSLATION, gather_extension_files
from translate_utils.infrastructure.updater import update_readme_progress
from translate_utils.presentation.cli.args import check_translation_progress_parse_args
from translate_utils.presentation.visualize.markdown import ProgressMarkdownReport
from translate_utils.presentation.visualize.mixins import ProgressReportData
from translate_utils.presentation.visualize.terminal import ProgressTerminalReport
from translate_utils.services.orchestrators import BatchProgressOrchestrator
from translate_utils.services.progress_service import ProgressService

LOGGER = setup_logging("TranslationProgress")


def check_translation_progress() -> None:
    args = check_translation_progress_parse_args()

    if not args.filepaths:
        paths_to_check = [DEFAULT_DIR_FOR_TRANSLATION]
        LOGGER.info(f"No path provided. Defaulting to: {DEFAULT_DIR_FOR_TRANSLATION}")
    else:
        paths_to_check = [Path(p) for p in args.filepaths]

    file_reader = CachedFileReader(read_renpy_file)

    text_processor = RenpyProcessor()
    specification = IsNotEmptySpec() & (
        IsSymbolOnlySpec(text_processor) | (
            IsDifferentSpec() & HasTargetAlphabetSpec() # & NoMixedAlphabetsSpec(text_processor)
        )
    )
    progress_counter=RegexProgressCounter(
                validator=TranslationValidator(specification),
                dialogues_config=RE_TRANSLATE_CONFIG,
                strings_config=RE_STRINGS_CONFIG
            )

    progress_service = ProgressService(
        file_reader=file_reader,
        progress_counter=progress_counter
    )
    orchestrator = BatchProgressOrchestrator(
        progress_service,
        lambda: concurrent.futures.ProcessPoolExecutor()
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
            LOGGER.warning(f"  - {file_name}: {error_message}")

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
