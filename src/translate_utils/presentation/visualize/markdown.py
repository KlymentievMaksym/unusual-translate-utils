import itertools
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from tabulate import tabulate

from translate_utils.presentation.visualize.mixins import (
    DialogueReportData,
    ProgressReportData,
    ReportDataMixin,
    StringReportData,
)
from translate_utils.presentation.visualize.utils import truncate

TData = TypeVar("TData", bound=ReportDataMixin)


class BaseMarkdownReport(ABC, Generic[TData]):
    def __init__(self, data: TData):
        self._data = data

    def generate(self, **kwargs: Any) -> str:
        if self._data.is_empty():
            return f"*({self._data.empty_message()})*\n"

        table = tabulate(
            self._get_rows(), headers=self._get_headers(), **self._default_kwargs(), **kwargs
        )

        if self._data.is_overflow():
            table += f"\n\n*({self._data.overflow_message()})*\n"

        return table

    def _default_kwargs(self) -> dict[str, Any]:
        return {"tablefmt": "github"}

    @abstractmethod
    def _get_headers(self) -> list[str]: ...
    @abstractmethod
    def _get_rows(self) -> list[list[str]]: ...


class DialogueMarkdownReport(BaseMarkdownReport[DialogueReportData]):
    """Generates a Markdown table string for parsed dialogues."""

    def _get_headers(self) -> list[str]:
        return ["Label", "Original Char", "Translated Char", "Original Text", "Translated Text"]

    def _get_rows(self) -> list[list[str]]:
        return [
            [
                label,
                data.original_character or "-",
                data.translation_character or "-",
                truncate(data.original_text, 40),
                truncate(data.translation_text, 40),
            ]
            for label, data in itertools.islice(self._data.dialogues.items(), self._data.limit)
        ]


class StringMarkdownReport(BaseMarkdownReport[StringReportData]):
    """Generates a Markdown table string for parsed UI strings."""

    def _get_headers(self) -> list[str]:
        return ["Original String", "New String"]

    def _get_rows(self) -> list[list[str]]:
        return [
            [truncate(old, 50), truncate(new, 50)]
            for old, new in itertools.islice(self._data.ui_strings.items(), self._data.limit)
        ]


class ProgressMarkdownReport(BaseMarkdownReport[ProgressReportData]):
    """Generates a Markdown table string for translation progress."""

    def _get_headers(self) -> list[str]:
        return [
            "File Name",
            "Statistics (Total)",
            "Statistics (Dialogues)",
            "Statistics (Strings)",
            "Progress",
        ]

    def _get_rows(self) -> list[list[str]]:
        rows = []

        for filename, translation_status in self._data.records.items():
            total = translation_status.total
            dialogues = translation_status.dialogues
            strings = translation_status.strings

            total_stats_str = f"{total.translated:>6} / {total.total:>6}"
            dialogues_stats_str = f"{dialogues.translated:>6} / {dialogues.total:>6}"
            strings_stats_str = f"{strings.translated:>6} / {strings.total:>6}"

            rows.append(
                [
                    filename,
                    total_stats_str,
                    dialogues_stats_str,
                    strings_stats_str,
                    f"{total.percentage:.2f}%",
                ]
            )

        global_total = self._data.translation_stats.global_total
        if not global_total.is_empty:
            rows.append(
                [
                    "**GLOBAL TOTAL**",
                    f"**{global_total.translated} / {global_total.total}**",
                    "**-**",
                    "**-**",
                    f"**{global_total.percentage:.2f}%**",
                ]
            )

        return rows

    def _default_kwargs(self) -> dict[str, Any]:
        default = super()._default_kwargs()
        default.update({"colalign": ("left", "right", "right", "right", "right")})
        return default
