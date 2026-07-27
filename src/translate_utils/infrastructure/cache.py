import functools
from multiprocessing.managers import DictProxy
from pathlib import Path
from typing import Callable, Generic, TypeVar

from translate_utils.core.exceptions import TranslationReadError
from translate_utils.core.interfaces import ReadStrategy
from translate_utils.infrastructure.cache_models import FileCache
from translate_utils.infrastructure.logger import get_logger

LOGGER = get_logger(__name__)

T_out = TypeVar('T_out')


def multiprocess_cache(shared_dict: DictProxy) -> Callable:
    """
    Decorator that uses a multiprocessing.Manager dictionary
    to share cached results across different processes.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(filepath: str | Path, *args, **kwargs) -> str:
            path_str = str(filepath)

            # Check shared memory proxy
            if path_str not in shared_dict:
                # Cache miss: execute function and store result in IPC dict
                shared_dict[path_str] = func(filepath, *args, **kwargs)

            return shared_dict[path_str]
        return wrapper
    return decorator

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
            self._cache[path_key] = FileCache(
                mtime=current_mtime,
                content=content
            )
            return content
        except OSError as e:
            text_to_report = f"Failed to read file {path_key}: {e}"
            LOGGER.error(text_to_report)
            raise TranslationReadError(text_to_report) from e
