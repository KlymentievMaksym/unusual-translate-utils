from abc import ABC, abstractmethod

from translate_utils.core.entities import DialogueLine, Progress

class ReportDataMixin(ABC):
    """Shared item/empty/overflow bookkeeping for any report renderer."""
    _raw_limit: int = -1

    @property
    @abstractmethod
    def records(self) -> dict: ...

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
    def __init__(self, dialogues: dict[str, DialogueLine], limit=15):
        self.dialogues = dialogues
        self._raw_limit = limit

    @property
    def records(self): return self.dialogues
    @property
    def report_name(self): return "Parsed Dialogues"

class StringReportData(ReportDataMixin):
    def __init__(self, ui_strings: dict[str, str], limit=15):
        self.ui_strings = ui_strings
        self._raw_limit = limit

    @property
    def records(self): return self.ui_strings
    @property
    def report_name(self): return "Parsed UI Strings"

class ProgressReportData(ReportDataMixin):
    def __init__(self, file_stats: dict, global_translated: int, global_total: int, dialog_progresses: list[Progress], string_progresses: list[Progress]) -> None:
        self.file_stats = file_stats
        self.global_translated = global_translated
        self.global_total = global_total
        self.dialog_progresses = dialog_progresses
        self.string_progresses = string_progresses

    @property
    def records(self): return self.file_stats
    @property
    def report_name(self): return "Translation Progress Report"
    @property
    def global_percent(self) -> float:
        return (self.global_translated / self.global_total) * 100 if self.global_total > 0 else 0.0
