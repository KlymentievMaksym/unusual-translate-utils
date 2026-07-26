from __future__ import annotations

from dataclasses import dataclass, field


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
            translated=self.translated + other.translated,
            total=self.total + other.total
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
