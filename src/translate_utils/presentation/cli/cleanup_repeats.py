from pathlib import Path

from translate_utils.core.exceptions import FileError
from translate_utils.core.interfaces import CleanStrategy
from translate_utils.core.replacer_methods import AVAILABLE_METHODS, CleanMethod
from translate_utils.infrastructure.composition.factories import create_default_cleaner
from translate_utils.infrastructure.filesystem.io import (
    gather_extension_files,
    read_renpy_file,
    write_renpy_file,
)
from translate_utils.infrastructure.filesystem.path import initialize_config
from translate_utils.infrastructure.logging.logger import get_logger, setup_logging
from translate_utils.infrastructure.parsing.renpy.parser import RegexDialogueParser
from translate_utils.infrastructure.parsing.renpy.regexes import RE_TRANSLATE_CONFIG
from translate_utils.presentation.cli.args import cleanup_repeats_parse_args
from translate_utils.services.cleanup_service import CleanupService
from translate_utils.services.mappers import build_reverse_lookup

LOGGER = get_logger("CleanupRepeats")


def cleanup_repeats() -> None:
    args = cleanup_repeats_parse_args()
    config = initialize_config()
    setup_logging("CleanupRepeats", config.paths.common_logs_dir)

    LOGGER.info("Starting cleanup process...")

    if not args.filepaths:
        LOGGER.warning("No filepaths provided. Nothing to clean.")
        return

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

    LOGGER.info(f"Loading and parsing: {args.filepaths}")

    rpy_files = gather_extension_files([Path(p) for p in args.filepaths], "rpy")
    if not rpy_files:
        LOGGER.warning("No .rpy files found to process.")
        return

    if args.name is not None and len(rpy_files) > 1:
        LOGGER.error("Cannot use --name output override when processing multiple files.")
        return

    cleaner = create_default_cleaner()
    clean_service = CleanupService(
        file_reader=read_renpy_file,
        file_parser=RegexDialogueParser(RE_TRANSLATE_CONFIG),
        file_cleaner=cleaner,
        file_writer=write_renpy_file,
        mapper=build_reverse_lookup,
    )

    LOGGER.info(f"Found {len(rpy_files)} files. Running cleanup...")
    success_count = 0
    for rpy_file in rpy_files:
        try:
            clean_service.clean_and_save(
                filepath=rpy_file, new_name=args.name, clean_method=clean_method
            )
            success_count += 1
        except FileError as e:
            LOGGER.error(f"Skipped {rpy_file} due to file error: {e}")
        except Exception as e:
            LOGGER.critical(f"Unexpected fatal error processing {rpy_file}: {e}", exc_info=True)

    LOGGER.info(f"Cleanup done. Processed {success_count}/{len(rpy_files)} files.")


if __name__ == "__main__":
    cleanup_repeats()
