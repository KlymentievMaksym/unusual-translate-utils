import re
from collections.abc import Mapping
from pathlib import Path
from typing import Protocol, TypeVar

from translate_utils.core.entities import DialogueLine, ExtractorParams, FileProgressSummary

T_in = TypeVar("T_in", contravariant=True)
T_out = TypeVar("T_out", covariant=True)


class TextProcessor(Protocol):
    """Protocol for domain-level text manipulation (e.g., removing tags)."""

    def strip_tags(self, text: str) -> str: ...
    def extract_words(self, text: str) -> list[str]: ...


class CleanStrategy(Protocol):
    """
    Strategy for cleaning or modifying extracted text blocks.
    Positional-only arguments (/) ensure the caller doesn't rely on arg names.
    """

    def __call__(self, text: str, indent: str, comment: str, /) -> str: ...


class ParseStrategy(Protocol[T_out]):
    """Strategy for parsing entire files into specific domain entities."""

    def __call__(self, file_text: str) -> T_out: ...


class ReadStrategy(Protocol[T_out]):
    """Defines how to read data from a storage medium."""

    def __call__(self, filepath: str | Path) -> T_out: ...


class WriteStrategy(Protocol[T_in]):
    """Defines how to write data to a storage medium."""

    def __call__(self, filepath: str | Path, content: T_in) -> None: ...


class MatchExtractorFunc(Protocol):
    """Extracts required domain parameters from a single regex match."""

    def __call__(self, match: re.Match[str]) -> ExtractorParams: ...


class ProgressCounterFunc(Protocol):
    """Counts translation progress for a given file text."""

    def __call__(self, file_text: str) -> FileProgressSummary: ...


class ReverseLookupMapper(Protocol):
    """Maps complex domain dialogue entities to a primitive lookup dictionary."""

    def __call__(self, dialogues: Mapping[str, DialogueLine]) -> dict[str, tuple[str, ...]]: ...
