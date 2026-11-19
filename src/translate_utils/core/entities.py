from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class LineRange:
    start: int = 1
    end: int | None = None

    def overlaps(self, block_start: int, block_end: int) -> bool:
        if block_end < self.start:
            return False
        return not (self.end is not None and block_start > self.end)


@dataclass(slots=True, frozen=True)
class Progress:
    translated: int = 0
    total: int = 0

    @property
    def percentage(self) -> float:
        if self.total == 0:
            return 0.0
        return round((self.translated / self.total) * 100, 2)

    @property
    def is_empty(self) -> bool:
        return self.total == 0

    def __add__(self, other: object) -> Progress:
        if not isinstance(other, Progress):
            return NotImplemented
        return Progress(
            translated=self.translated + other.translated, total=self.total + other.total
        )


@dataclass(slots=True, frozen=True)
class DialogueLine:
    script_position: str
    script_label: str
    script_hash: str
    original_character: str | None
    original_text: str
    translation_character: str | None
    translation_text: str
    start_line: int = 0
    end_line: int = 0


@dataclass(frozen=True, slots=True)
class ExtractorParams:
    full_text: str
    indent: str
    original_text: str


@dataclass(frozen=True, slots=True)
class CleanResults:
    cleaned_text: str
    replaced_count: int


@dataclass(frozen=True, slots=True)
class FileProgressSummary:
    total: Progress
    dialogues: Progress
    strings: Progress

    @property
    def is_empty(self) -> bool:
        return self.total.is_empty


@dataclass(frozen=True, slots=True)
class FileStats:
    name: str
    summary: FileProgressSummary


@dataclass(frozen=True, slots=True)
class TranslationStats:
    file_details: dict[str, FileProgressSummary] = field(default_factory=dict)
    global_total: Progress = field(default_factory=Progress)
    failed_files: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TranslationsDicts:
    dialogues: dict[str, DialogueLine]
    strings: dict[str, str]
    string_lines: dict[str, tuple[int, int]] = field(default_factory=dict)


@dataclass
class LanguageMatch:
    key: str
    message: str
    rule_id: str
    replacements: list[str]
    context_text: str
    original_text: str
    offset: int
    length: int
    issue_type: str
    category_id: str


@dataclass
class FileCheckResult:
    filepath: Path
    matches: dict[str, list[LanguageMatch]] = field(default_factory=dict)
    is_filtered: bool = False

    @property
    def log_filename(self) -> str:
        suffix = "_specified.log" if self.is_filtered else ".log"
        return f"{self.filepath.stem}{suffix}"


@dataclass
class LanguageCheckResults:
    file_results: list[FileCheckResult] = field(default_factory=list)
    failed_files: dict[str, str] = field(default_factory=dict)

    @property
    def total_issues(self) -> int:
        return sum(len(res.matches) for res in self.file_results)


@dataclass(frozen=True, slots=True)
class ReplacementEntity:
    global_offset: int
    word: str


@dataclass(frozen=True, slots=True)
class RuleEntity:
    id: str
    message: str
