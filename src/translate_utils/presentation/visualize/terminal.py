import itertools
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from rich.console import Console
from rich.table import Table

from translate_utils.presentation.color import get_color_gradient
from translate_utils.presentation.visualize.mixins import (
    DialogueReportData,
    LanguageCheckReportData,
    ProgressReportData,
    ReportDataMixin,
    StringReportData,
)
from translate_utils.presentation.visualize.utils import truncate

TData = TypeVar("TData", bound=ReportDataMixin)
CONSOLE = Console()


class BaseTerminalReport(ABC, Generic[TData]):
    def __init__(self, data: TData):
        self._data = data

    def generate(self) -> Table:
        table = self._create_empty_table()
        self._populate_table_rows(table)
        return table

    def display(self) -> None:
        if self._data.is_empty():
            CONSOLE.print(f"[yellow]--- {self._data.empty_message()} ---[/yellow]\n")
            return
        table = self.generate()
        CONSOLE.print(table)
        if self._data.is_overflow():
            CONSOLE.print(f"[dim]{self._data.overflow_message()}[/dim]\n")

    @abstractmethod
    def _create_empty_table(self) -> Table: ...
    @abstractmethod
    def _populate_table_rows(self, table: Table) -> None: ...


class DialogueTerminalReport(BaseTerminalReport[DialogueReportData]):
    """Generates and Renders the parsed dialogues as a Rich table in the terminal."""

    def _create_empty_table(self) -> Table:
        table = Table(title="Parsed Dialogues", show_header=True, header_style="bold magenta")

        table.add_column("Label", style="cyan", no_wrap=True)
        table.add_column("Char", style="green", justify="center")
        table.add_column("Original Char", style="yellow")
        table.add_column("Translated Char", style="blue")
        table.add_column("Original Text", style="yellow")
        table.add_column("Translated Text", style="blue")

        return table

    def _populate_table_rows(self, table: Table) -> None:
        for label, data in itertools.islice(self._data.dialogues.items(), self._data.limit):
            original_char = data.original_character or "-"
            translation_char = data.translation_character or "-"
            table.add_row(
                label,
                original_char,
                translation_char,
                truncate(data.original_text, 40),
                truncate(data.translation_text, 40),
            )


class StringTerminalReport(BaseTerminalReport[StringReportData]):
    """Renders the parsed UI strings as a Rich table in the terminal."""

    def _create_empty_table(self) -> Table:
        table = Table(title="Parsed UI Strings", show_header=True, header_style="bold magenta")

        table.add_column("Original String", style="yellow")
        table.add_column("New String", style="blue")

        return table

    def _populate_table_rows(self, table: Table) -> None:
        for old, new in itertools.islice(self._data.ui_strings.items(), self._data.limit):
            table.add_row(truncate(old, 50), truncate(new, 50))


class ProgressTerminalReport(BaseTerminalReport[ProgressReportData]):
    """Renders the translation progress as a Rich table in the terminal."""

    def _create_empty_table(self) -> Table:
        table = Table(
            title="Translation Progress Report", show_header=True, header_style="bold magenta"
        )

        table.add_column("File Name", style="cyan")
        table.add_column("Statistics (Total)", justify="right", style="white")
        table.add_column("Statistics (Dialogues)", justify="right", style="white")
        table.add_column("Statistics (Strings)", justify="right", style="white")
        table.add_column("Progress", justify="right", style="green")

        return table

    def _populate_table_rows(self, table: Table) -> None:
        for filename, translation_status in self._data.records.items():
            total = translation_status.total
            dialogues = translation_status.dialogues
            strings = translation_status.strings

            total_stats_str = f"{total.translated:>6} / {total.total:>6}"
            dialogues_stats_str = f"{dialogues.translated:>6} / {dialogues.total:>6}"
            strings_stats_str = f"{strings.translated:>6} / {strings.total:>6}"
            pct_str = f"{total.percentage:>6.2f}%"

            pct_color = get_color_gradient(total.percentage)
            table.add_row(
                filename,
                total_stats_str,
                dialogues_stats_str,
                strings_stats_str,
                f"[{pct_color}]{pct_str}[/{pct_color}]",
            )

        global_total = self._data.translation_stats.global_total
        if not global_total.is_empty:
            table.add_section()
            table.add_row(
                "[bold]GLOBAL TOTAL[/bold]",
                f"[bold]{global_total.translated:>6} / {global_total.total:>6}[/bold]",
                "[bold]-[/bold]",
                "[bold]-[/bold]",
                f"[bold cyan]{global_total.percentage:>6.2f}%[/bold cyan]",
            )

class LanguageCheckTerminalReport(BaseTerminalReport[LanguageCheckReportData]):
    """Renders LanguageTool inspection results as a Rich table in the terminal."""

    def _create_empty_table(self) -> Table:
        table = Table(
            title="LanguageTool Inspection Report",
            show_header=True,
            header_style="bold magenta",
        )

        table.add_column("File", style="cyan")
        table.add_column("Key", style="yellow")
        table.add_column("Rule ID", style="red")
        table.add_column("Message", style="white")
        table.add_column("Context", style="dim")
        table.add_column("Suggestions", style="green")

        return table

    def _populate_table_rows(self, table: Table) -> None:
        for _, (filename, match) in itertools.islice(
            self._data.records.items(), self._data.limit
        ):
            suggestions_str = (
                ", ".join(match.replacements) if match.replacements else "-"
            )
            table.add_row(
                filename,
                # truncate(match.key, 20),
                match.key,
                match.rule_id,
                match.message,
                match.context_text,
                suggestions_str,
                # truncate(match.message, 40),
                # truncate(match.context_text, 40),
                # truncate(suggestions_str, 30),
            )
