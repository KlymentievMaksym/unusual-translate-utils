import concurrent.futures
from pathlib import Path

from translate_utils.infrastructure.cache import CachedFileReader
from translate_utils.infrastructure.factories import create_default_parser
from translate_utils.infrastructure.io import gather_extension_files, read_renpy_file
from translate_utils.infrastructure.language_tool import LanguageToolClient
from translate_utils.infrastructure.logger import setup_logging
from translate_utils.infrastructure.parsers.processors import RenpyProcessor
from translate_utils.infrastructure.path import DEFAULT_DIR_FOR_TRANSLATION
from translate_utils.presentation.cli.args import check_language_parse_args
from translate_utils.presentation.visualize.mixins import LanguageCheckReportData
from translate_utils.presentation.visualize.terminal import LanguageCheckTerminalReport
from translate_utils.services.language_check_service import LanguageCheckService
from translate_utils.services.orchestrators import BatchLanguageCheckOrchestrator

LOGGER = setup_logging("CheckLanguage")


def check_language() -> None:
    LOGGER.info("Starting language check process...")
    args = check_language_parse_args()

    if not args.filepaths:
        paths_to_check = [DEFAULT_DIR_FOR_TRANSLATION]
        LOGGER.info(f"No path provided. Defaulting to: {DEFAULT_DIR_FOR_TRANSLATION}")
    else:
        paths_to_check = [Path(p) for p in args.filepaths]

    rpy_files = gather_extension_files(paths_to_check, "rpy")

    if not rpy_files:
        LOGGER.warning("No .rpy files found to process.")
        return

    LOGGER.info(f"Found {len(rpy_files)} files. Running LanguageTool checks...")

    file_reader = CachedFileReader(read_renpy_file)
    parser = create_default_parser()
    checker = LanguageToolClient(
        api_url=args.api_url,
        api_username=args.api_username,
        api_key=args.api_key,
        language=args.language,
        disabled_rules=args.disabled_rules,
    )

    check_service = LanguageCheckService(
        file_reader=file_reader,
        file_parser=parser,
        language_checker=checker,
        processor=RenpyProcessor(),
        item_workers=args.max_workers
    )

    orchestrator = BatchLanguageCheckOrchestrator(
        service=check_service,
        executor_factory=lambda: concurrent.futures.ThreadPoolExecutor(
            max_workers=args.max_workers
        ),
    )

    results = orchestrator.execute(rpy_files)

    progress_data = LanguageCheckReportData(results)
    LanguageCheckTerminalReport(progress_data).display()

    if results.failed_files:
        LOGGER.warning(f"Encountered errors in {len(results.failed_files)} files:")
        for file_name, error_message in results.failed_files.items():
            LOGGER.warning(f" - {file_name}: {error_message}")


if __name__ == "__main__":
    check_language()
