from pathlib import Path

from translate_utils.core.exceptions import FileError
from translate_utils.core.interfaces import CleanStrategy
from translate_utils.core.replacer_methods import AVAILABLE_METHODS, CleanMethod
from translate_utils.infrastructure.factories import create_default_cleaner
from translate_utils.infrastructure.io import read_renpy_file, write_renpy_file
from translate_utils.infrastructure.logger import setup_logging
from translate_utils.infrastructure.parser import RegexDialogueParser
from translate_utils.infrastructure.parsers.regexes import RE_TRANSLATE_CONFIG
from translate_utils.presentation.cli.args import cleanup_repeats_parse_args
from translate_utils.services.cleanup_service import CleanupService
from translate_utils.services.mappers import build_reverse_lookup

LOGGER = setup_logging("CleanupRepeats")


def cleanup_repeats() -> None:
    LOGGER.info("Starting cleanup process...")
    args = cleanup_repeats_parse_args()
    if not args.is_suitable_clean_method():
        available_methods_str = ", ".join(AVAILABLE_METHODS)
        LOGGER.warning(
            f"Clean method '{args.clean_method}' is not supported. "
            f"Available methods: [{available_methods_str}]. "
            f"Defaulting to '{CleanMethod.ONLY_COMMENT}'..."
        )

    clean_method: CleanStrategy = AVAILABLE_METHODS.get(
        args.clean_method, AVAILABLE_METHODS[CleanMethod.ONLY_COMMENT]
    )

    cleaner = create_default_cleaner()
    clean_service = CleanupService(
        file_reader=read_renpy_file,
        file_parser=RegexDialogueParser(RE_TRANSLATE_CONFIG),
        file_cleaner=cleaner,
        file_writer=write_renpy_file,
        mapper=build_reverse_lookup,
    )

    if not args.filepaths:
        LOGGER.info("There is no filepath given")
        return

    LOGGER.info(f"Loading and parsing: {args.filepaths}...")
    success_count = 0
    for filepath in args.filepaths:
        _filepath = Path(filepath)
        try:
            if _filepath.is_file():
                clean_service.clean_and_save(
                    filepath=filepath, new_name=args.name, clean_method=clean_method
                )
            else:
                for file_path in _filepath.glob("*.rpy"):
                    clean_service.clean_and_save(
                        filepath=file_path, new_name=args.name, clean_method=clean_method
                    )
            success_count += 1
        except FileError as e:
            LOGGER.error(f"Skipped {filepath} due to file error: {e}")
        except Exception as e:
            LOGGER.critical(f"Unexpected fatal error processing {filepath}: {e}", exc_info=True)


if __name__ == "__main__":
    cleanup_repeats()
