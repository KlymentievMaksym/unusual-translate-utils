from pathlib import Path

from translate_utils.infrastructure.logger import get_logger

LOGGER = get_logger(__name__)


class FileManager:
    @staticmethod
    def read_renpy_file(filepath: str | Path) -> str:
        """Read content of renpy file"""
        try:
            return Path(filepath).read_text(encoding='utf-8-sig')
        except OSError as e:
            LOGGER.error(f"Failed to read {filepath}: {e}")
            raise

    @staticmethod
    def write_renpy_file(filepath: str | Path, content: str) -> None:
        """Rewrite content of renpy file"""
        try:
            Path(filepath).write_text(content, encoding='utf-8-sig')
        except OSError as e:
            LOGGER.error(f"Failed to write {filepath}: {e}")
            raise

