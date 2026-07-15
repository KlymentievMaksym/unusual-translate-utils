from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from rich.console import Console
from rich.table import Table

from translate_utils.presentation.visualize.utils import truncate
from translate_utils.presentation.color import get_color_gradient
from translate_utils.presentation.visualize.mixins import ReportDataMixin, DialogueReportData, StringReportData, ProgressReportData


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
        table.add_column("Original Text", style="yellow")
        table.add_column("Translated Text", style="blue")

        return table

    def _populate_table_rows(self, table: Table) -> None:
        for label, data in list(self._data.dialogues.items())[:self._data.limit]:
            char = data.character if data.character else "-"
            table.add_row(label, char, truncate(data.original, 40), truncate(data.translated, 40))

class StringTerminalReport(BaseTerminalReport[StringReportData]):
    """Renders the parsed UI strings as a Rich table in the terminal."""
    def _create_empty_table(self) -> Table:
        table = Table(title="Parsed UI Strings", show_header=True, header_style="bold magenta")

        table.add_column("Original String", style="yellow")
        table.add_column("New String", style="blue")

        return table

    def _populate_table_rows(self, table: Table) -> None:
        for old, new in list(self._data.ui_strings.items())[:self._data.limit]:
            table.add_row(truncate(old, 50), truncate(new, 50))

class ProgressTerminalReport(BaseTerminalReport[ProgressReportData]):
    """Renders the translation progress as a Rich table in the terminal."""
    def _create_empty_table(self) -> Table:
        table = Table(title="Translation Progress Report", show_header=True, header_style="bold magenta")

        table.add_column("File Name", style="cyan")
        table.add_column("Statistics (Total)", justify="right", style="white")
        table.add_column("Statistics (Dialogues)", justify="right", style="white")
        table.add_column("Statistics (Strings)", justify="right", style="white")
        table.add_column("Progress", justify="right", style="green")

        return table

    def _populate_table_rows(self, table: Table) -> None:
        combined_data = zip(self._data.file_stats.items(), self._data.dialog_progresses, self._data.string_progresses)
        for (filename, (translated, total)), dialog, string in combined_data:
            percent = (translated / total) * 100 if total > 0 else 0
            total_stats_str = f"{translated:>6} / {total:>6}"
            dialogues_stats_str = f"{dialog.translated:>6} / {dialog.total:>6}"
            strings_stats_str = f"{string.translated:>6} / {string.total:>6}"
            pct_str = f"{percent:>6.2f}%"

            pct_color = get_color_gradient(percent)
            table.add_row(filename, total_stats_str, dialogues_stats_str, strings_stats_str, f"[{pct_color}]{pct_str}[/{pct_color}]")
        
        if self._data.global_total > 0:
            table.add_section()
            table.add_row(
                "[bold]GLOBAL TOTAL[/bold]", 
                f"[bold]{self._data.global_translated:>6} / {self._data.global_total:>6}[/bold]", 
                f"[bold]-[/bold]", 
                f"[bold]-[/bold]", 
                f"[bold cyan]{self._data.global_percent:>6.2f}%[/bold cyan]"
            )
