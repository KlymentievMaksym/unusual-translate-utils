import concurrent.futures
from collections import defaultdict
from pathlib import Path

from translate_utils.core.entities import ReplacementEntity, RuleEntity
from translate_utils.core.rules import IsSymbolOnlySpec
from translate_utils.infrastructure.cache import CachedFileReader
from translate_utils.infrastructure.factories import create_default_parser, create_default_validator
from translate_utils.infrastructure.io import (
    gather_extension_files,
    read_renpy_file,
    write_renpy_file,
)
from translate_utils.infrastructure.language_tool import LanguageToolClient
from translate_utils.infrastructure.logger import setup_logging
from translate_utils.infrastructure.parsers.processors import RenpyProcessor
from translate_utils.infrastructure.path import (
    DEFAULT_DIR_FOR_CHECK_LOGS,
    DEFAULT_DIR_FOR_TRANSLATION,
    DEFAULT_LANGUAGE_EXCEPTIONS_FILE,
)
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

    LOGGER.info(f"Found {len(rpy_files)} files. Running LanguageTool checks...")

    file_reader = CachedFileReader(read_renpy_file)
    dicts = (
        args.dicts
        if args.dicts != []
        else file_reader(DEFAULT_LANGUAGE_EXCEPTIONS_FILE).splitlines()
    )
    LOGGER.info(f"Ignoring words: {dicts}")

    parser = create_default_parser()
    checker = LanguageToolClient(
        api_url=args.api_url,
        api_username=args.api_username,
        api_key=args.api_key,
        language=args.language,
        disabled_rules=args.disabled_rules,
        dicts=dicts,
        max_workers=args.max_workers
    )
    dicts = list(dct.lower() for dct in dicts) if dicts is not None else []

    validator = create_default_validator()

    check_service = LanguageCheckService(
        file_reader=file_reader,
        file_parser=parser,
        language_checker=checker,
        processor=RenpyProcessor(),
        validator=validator,
        item_workers=args.max_workers
    )

    orchestrator = BatchLanguageCheckOrchestrator(
        service=check_service,
        executor_factory=lambda: concurrent.futures.ThreadPoolExecutor(
            max_workers=args.max_workers
        ),
    )

    results = orchestrator.execute(rpy_files)
    LOGGER.info("Check done")

    next_line = '\n'
    global_separator = "=" * 10 + next_line
    local_separator = "_" * 10 + next_line

    for file_results in results.file_results:
        text = global_separator
        for key, matches in file_results.matches.items():
            match = matches[0]
            text += "Key: " + key + next_line
            text += local_separator
            context_text = match.original_text

            text += context_text + next_line

            replacements: dict[ReplacementEntity, list] = defaultdict(list)
            rules: dict[ReplacementEntity, RuleEntity] = defaultdict()
            underliner = list(" " * len(context_text))

            for match in matches:

                offset = match.offset

                flagged_word = match.context_text[offset:offset+match.length].lower()
                if flagged_word in dicts:
                    continue

                if (
                    match.rule_id == "COMMA_PARENTHESIS_WHITESPACE"
                    and IsSymbolOnlySpec(RenpyProcessor()).is_satisfied_by(flagged_word, "")
                ):
                    continue

                global_offset = offset

                replacement_entity = ReplacementEntity(
                    global_offset=global_offset,
                    word=flagged_word
                )

                rule_entity = RuleEntity(
                    id=match.rule_id,
                    message=match.message
                )

                underliner[global_offset:global_offset+match.length] = '-' * match.length
                replacements[replacement_entity].extend(match.replacements)
                rules[replacement_entity] = rule_entity

            text += "".join(underliner) + next_line

            text += local_separator
            for (_replacement_entity, _replacement), _rule_entity in zip(
                replacements.items(),
                rules.values(),
                strict=True
            ):
                text += (
                    f"{_replacement_entity.word}:{_replacement_entity.global_offset}: "
                    f"{', '.join(_replacement)}"
                ) + next_line
                text += "Rule id: " + _rule_entity.id + next_line
                text += "Rule message: " + _rule_entity.message + next_line
                text += local_separator

            text += next_line + global_separator

        result_file = Path(file_results.filepath).stem + ".log"
        write_renpy_file(DEFAULT_DIR_FOR_CHECK_LOGS / result_file, text)

        LOGGER.info(f"Saved {file_results.filepath} results to {result_file}")

    # progress_data = LanguageCheckReportData(results)
    # LanguageCheckTerminalReport(progress_data).display()

    if results.failed_files:
        LOGGER.warning(f"Encountered errors in {len(results.failed_files)} files:")
        for file_name, error_message in results.failed_files.items():
            LOGGER.warning(f" - {file_name}: {error_message}")

if __name__ == "__main__":
    check_language()
