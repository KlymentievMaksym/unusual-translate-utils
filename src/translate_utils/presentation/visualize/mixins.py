from abc import ABC, abstractmethod
from typing import Any

from translate_utils.core.entities import DialogueLine, FileProgressSummary, TranslationStats


class ReportDataMixin(ABC):
    """Shared item/empty/overflow bookkeeping for any report renderer."""
    _raw_limit: int = -1

    @property
    @abstractmethod
    def records(self) -> dict[str, Any]: ...

    @property
    @abstractmethod
    def report_name(self) -> str: ...

    @property
    def limit(self) -> int:
        return len(self.records) if self._raw_limit == -1 else self._raw_limit

    def is_empty(self) -> bool:
        return not self.records

    def is_overflow(self) -> bool:
        return len(self.records) > self.limit

    def empty_message(self) -> str:
        return f"{self.report_name} (Empty)"

    def overflow_message(self) -> str:
        return f"... and {len(self.records) - self.limit} more rows."

class DialogueReportData(ReportDataMixin):
    def __init__(self, dialogues: dict[str, DialogueLine], limit: int = 15) -> None:
        self.dialogues = dialogues
        self._raw_limit = limit

    @property
    def records(self) -> dict[str, DialogueLine]: return self.dialogues
    @property
    def report_name(self) -> str: return "Parsed Dialogues"

class StringReportData(ReportDataMixin):
    def __init__(self, ui_strings: dict[str, str], limit: int = 15) -> None:
        self.ui_strings = ui_strings
        self._raw_limit = limit

    @property
    def records(self) -> dict[str, str]: return self.ui_strings
    @property
    def report_name(self) -> str: return "Parsed UI Strings"

class ProgressReportData(ReportDataMixin):
    def __init__(self, translation_stats: TranslationStats) -> None:
        self.translation_stats = translation_stats

    @property
    def records(self) -> dict[str, FileProgressSummary]: return self.translation_stats.file_details
    @property
    def report_name(self) -> str: return "Translation Progress Report"
