from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from tabulate import tabulate

from translate_utils.presentation.visualize.utils import truncate
from translate_utils.presentation.visualize.mixins import ReportDataMixin, DialogueReportData, StringReportData, ProgressReportData

TData = TypeVar("TData", bound=ReportDataMixin)

class BaseMarkdownReport(ABC, Generic[TData]):
    def __init__(self, data: TData):
        self._data = data

    def generate(self, **kwargs) -> str:
        if self._data.is_empty():
            return f"*({self._data.empty_message()})*\n"
        table = tabulate(self._get_rows(), headers=self._get_headers(), **{**self._default_kwargs(), **kwargs})
        if self._data.is_overflow():
            table += f"\n\n*({self._data.overflow_message()})*\n"
        return table

    def _default_kwargs(self) -> dict:
        return {"tablefmt": "github"}

    @abstractmethod
    def _get_headers(self) -> list[str]: ...
    @abstractmethod
    def _get_rows(self) -> list[list]: ...

class DialogueMarkdownReport(BaseMarkdownReport[DialogueReportData]):
    """Generates a Markdown table string for parsed dialogues."""
    def _get_headers(self) -> list[str]: return ["Label", "Char", "Original Text", "Translated Text"]
    def _get_rows(self) -> list[list]:
        return [
            [
                label, 
                data.character if data.character else "-", 
                truncate(data.original, 40), 
                truncate(data.translated, 40)
            ]
            for label, data in list(self._data.dialogues.items())[:self._data.limit]
        ]

class StringMarkdownReport(BaseMarkdownReport[StringReportData]):
    """Generates a Markdown table string for parsed UI strings."""
    def _get_headers(self) -> list[str]: return ["Original String", "New String"]
    def _get_rows(self) -> list[list]:
        return [
            [truncate(old, 50), truncate(new, 50)] 
            for old, new in list(self._data.ui_strings.items())[:self._data.limit]
        ]

class ProgressMarkdownReport(BaseMarkdownReport[ProgressReportData]):
    """Generates a Markdown table string for translation progress."""
    def _get_headers(self) -> list[str]: return ["File Name", "Statistics (Total)", "Statistics (Dialogues)", "Statistics (Strings)", "Progress"]
    def _get_rows(self) -> list[list]:
        rows = []

        combined_data = zip(self._data.file_stats.items(), self._data.dialog_progresses, self._data.string_progresses)
        for (filename, (translated, total)), dialog, string in combined_data:
            percent = (translated / total) * 100 if total > 0 else 0

            total_stats_str = f"{translated:>6} / {total:>6}"
            dialogues_stats_str = f"{dialog.translated:>6} / {dialog.total:>6}"
            strings_stats_str = f"{string.translated:>6} / {string.total:>6}"

            rows.append([filename, total_stats_str, dialogues_stats_str, strings_stats_str, f"{percent:.2f}%"])
        
        if self._data.global_total > 0:
            rows.append(["**GLOBAL TOTAL**", f"**{self._data.global_translated} / {self._data.global_total}**", f"**-**", f"**-**", f"**{self._data.global_percent:.2f}%**"])

        return rows

    def _default_kwargs(self) -> dict:
        default = super()._default_kwargs()
        default.update({"colalign":("left", "right", "right", "right", "right")})
        return default
