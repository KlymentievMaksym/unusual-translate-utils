import concurrent.futures

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
from translate_utils.infrastructure.filesystem.path import initialize_config
from translate_utils.infrastructure.language_tools.language_tool import LanguageToolClient
from translate_utils.infrastructure.language_tools.normalizers import StutterNormalizer
from translate_utils.infrastructure.logging.logger import get_logger, setup_logging
from translate_utils.infrastructure.parsing.renpy.processors import RenpyProcessor
from translate_utils.infrastructure.parsing.renpy.regexes import RE_SIMPLE_TAGS
from translate_utils.infrastructure.reporting.reporter import LanguageCheckLogReporter
from translate_utils.presentation.cli.args import check_language_parse_args
from translate_utils.presentation.cli.common import collect_paths
from translate_utils.services.language_check_service import LanguageCheckService
from translate_utils.services.orchestrators import BatchLanguageCheckOrchestrator

LOGGER = get_logger("CheckLanguage")


def check_language() -> None:
    args = check_language_parse_args()
    config = initialize_config()
    setup_logging("CheckLanguage", config.paths.common_logs_dir)

    LOGGER.info("Starting language check process...")

    paths_to_check = collect_paths(
        args.filepaths,
        config.settings.dir_for_translation,
        config.paths.settings_file,
    )

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

    dicts = file_reader(config.paths.language_exceptions_file).splitlines()
    dicts = [dct.strip().lower() for dct in dicts if dct.strip()]
    LOGGER.info(f"Ignoring words: {dicts}")

    validator = create_default_validator()

    check_service = LanguageCheckService(
        file_reader=file_reader,
        file_parser=parser,
        language_checker=checker,
        processor=RenpyProcessor(RE_strip_tags=RE_SIMPLE_TAGS),
        validator=validator,
        normalizer=StutterNormalizer(),
        dicts=dicts,
        item_workers=args.items_workers,
    )

    reporter = LanguageCheckLogReporter(
        output_dir=config.paths.check_logs_dir, file_writer=write_renpy_file
    )

    orchestrator = BatchLanguageCheckOrchestrator(
        service=check_service,
        file_reporter=reporter,
        executor_factory=lambda: concurrent.futures.ThreadPoolExecutor(
            max_workers=args.file_workers
        ),
    )

    file_line_ranges = {
        rpy_file: ranges
        for rpy_file in rpy_files
        if (ranges := args.resolve_line_ranges(rpy_file)) is not None
    }

    try:
        results = orchestrator.execute(
            rpy_files,
            file_line_ranges=file_line_ranges,
            labels=args.labels,
            disable_check_strings=args.disable_check_strings,
        )
        LOGGER.info("Check done")
    except KeyboardInterrupt:
        LOGGER.error("Execution interrupted by user (Ctrl+C). Exiting clean.")
        return

    for file_result in results.file_results:
        result_path = config.paths.check_logs_dir
        LOGGER.info(
            f"Saved {len(file_result.matches)} results "
            f'from "{file_result.filepath}" '
            f"to {result_path / file_result.log_filename}"
        )

    if results.failed_files:
        LOGGER.warning(f"Encountered errors in {len(results.failed_files)} files:")
        for file_name, error_message in results.failed_files.items():
            LOGGER.warning(f" - {file_name}: {error_message}")


if __name__ == "__main__":
    check_language()
