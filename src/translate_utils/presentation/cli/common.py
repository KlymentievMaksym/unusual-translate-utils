from pathlib import Path

from translate_utils.infrastructure.logging.logger import get_logger

LOGGER = get_logger(__name__)


def collect_paths(
    filepaths: list[str], dir_for_translation: Path, settings_file: Path
) -> list[Path]:
    if not filepaths:
        paths_to_check = [dir_for_translation]
        LOGGER.info(
            f"No path provided. Defaulting to: {dir_for_translation} | "
            f"Can be changed in {settings_file}"
        )
    else:
        paths_to_check = [Path(p) for p in filepaths]
    return paths_to_check
