import concurrent.futures
from pathlib import Path

from translate_utils.infrastructure.caching.cache import CachedFileReader
from translate_utils.infrastructure.composition.factories import (
    create_default_parser,
    create_default_validator,
)
from translate_utils.infrastructure.filesystem.io import (
    gather_extension_files,
    read_renpy_file,
    write_renpy_file,
)
from translate_utils.infrastructure.filesystem.path import (
    DEFAULT_DIR_FOR_CHECK_LOGS,
    DEFAULT_DIR_FOR_TRANSLATION,
    DEFAULT_LANGUAGE_EXCEPTIONS_FILE,
)
from translate_utils.infrastructure.language_tools.language_tool import LanguageToolClient
from translate_utils.infrastructure.logging.logger import setup_logging
from translate_utils.infrastructure.parsing.renpy.processors import RenpyProcessor
from translate_utils.infrastructure.parsing.renpy.regexes import RE_SIMPLE_TAGS
from translate_utils.infrastructure.reporting.reporter import LanguageCheckLogReporter
from translate_utils.presentation.cli.args import check_language_parse_args
from translate_utils.services.language_check_service import LanguageCheckService
from translate_utils.services.orchestrators import BatchLanguageCheckOrchestrator

# from translate_utils.presentation.visualize.mixins import LanguageCheckReportData
# from translate_utils.presentation.visualize.terminal import LanguageCheckTerminalReport

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

    LOGGER.info(f"Found {len(rpy_files)} files. Running LanguageTool checks to {args.api_url}...")

    file_reader = CachedFileReader(read_renpy_file)

    parser = create_default_parser()

    checker = LanguageToolClient(
        api_url=args.api_url,
        api_username=args.api_username,
        api_key=args.api_key,
        language=args.language,
        disabled_rules=args.disabled_rules,
        dicts=args.dicts,
        max_workers=args.items_workers,
    )

    dicts = file_reader(DEFAULT_LANGUAGE_EXCEPTIONS_FILE).splitlines()
    dicts = list(dct.lower() for dct in dicts) if dicts is not None else dicts
    LOGGER.info(f"Ignoring words: {dicts}")

    validator = create_default_validator()

    check_service = LanguageCheckService(
        file_reader=file_reader,
        file_parser=parser,
        language_checker=checker,
        processor=RenpyProcessor(RE_strip_tags=RE_SIMPLE_TAGS),
        validator=validator,
        dicts=dicts,
        item_workers=args.items_workers,
    )

    reporter = LanguageCheckLogReporter(
        output_dir=DEFAULT_DIR_FOR_CHECK_LOGS, file_writer=write_renpy_file
    )

    orchestrator = BatchLanguageCheckOrchestrator(
        service=check_service,
        file_reporter=reporter,
        executor_factory=lambda: concurrent.futures.ThreadPoolExecutor(
            max_workers=args.file_workers
        ),
    )

    try:
        results = orchestrator.execute(rpy_files)
        LOGGER.info("Check done")
    except KeyboardInterrupt:
        LOGGER.error("Execution interrupted by user (Ctrl+C). Exiting clean.")
        return

    for file_result in results.file_results:
        result_file = file_result.filepath.stem + ".log"
        LOGGER.info(
            f"Saved {file_result.filepath} {len(file_result.matches)} results to {result_file}"
        )

    if results.failed_files:
        LOGGER.warning(f"Encountered errors in {len(results.failed_files)} files:")
        for file_name, error_message in results.failed_files.items():
            LOGGER.warning(f" - {file_name}: {error_message}")


if __name__ == "__main__":
    check_language()
