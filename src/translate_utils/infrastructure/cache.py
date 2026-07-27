from pathlib import Path
from typing import Generic, TypeVar

from translate_utils.core.exceptions import TranslationReadError
from translate_utils.core.interfaces import ReadStrategy
from translate_utils.infrastructure.cache_models import FileCache
from translate_utils.infrastructure.logger import get_logger

LOGGER = get_logger(__name__)

T_out = TypeVar("T_out")


class CachedFileReader(Generic[T_out]):
    """
    Decorator class that adds mtime-based caching to any file reading function.
    """

    def __init__(self, reader_func: ReadStrategy[T_out]) -> None:
        self._reader_func = reader_func
        self._cache: dict[Path, FileCache[T_out]] = {}

    def __call__(self, filepath: str | Path) -> T_out:
        path_key = Path(filepath)

        try:
            current_mtime = path_key.stat().st_mtime
        except OSError as e:
            text_to_report = f"Failed to access file stats for {path_key}: {e}"
            LOGGER.error(text_to_report)
            raise TranslationReadError(text_to_report) from e

        cached_entry = self._cache.get(path_key)
        if cached_entry is not None and cached_entry.mtime == current_mtime:
            return cached_entry.content

        try:
            content = self._reader_func(path_key)
            self._cache[path_key] = FileCache(mtime=current_mtime, content=content)
            return content
        except OSError as e:
            text_to_report = f"Failed to read file {path_key}: {e}"
            LOGGER.error(text_to_report)
            raise TranslationReadError(text_to_report) from e
