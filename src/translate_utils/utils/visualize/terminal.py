
from rich.console import Console
from rich.table import Table

from translate_utils.utils.visualize.utils import truncate
from translate_utils.utils.color import get_color_gradient


CONSOLE = Console()

# --- Print ---
def print_dialogue_console(dialogues: dict, limit: int = -1) -> None:
    """Renders the parsed dialogues as a Rich table in the terminal."""
    if not dialogues:
        CONSOLE.print("[yellow]--- Parsed Dialogues (Empty) ---[/yellow]\n")
        return
    table = generate_dialogue_table(dialogues, limit)
    CONSOLE.print(table)
    if len(dialogues) > limit:
        CONSOLE.print(f"[dim]... and {len(dialogues) - limit} more rows.[/dim]\n")

def print_progress_console(file_stats: dict, global_translated: int, global_total: int, dialog_progresses: list, string_progresses: list) -> None:
    """Renders the translation progress as a Rich table in the terminal."""
    if not file_stats:
        CONSOLE.print("[yellow]--- Translation Progress Report (Empty) ---[/yellow]\n")
        return

    table = generate_progress_table(file_stats, global_translated, global_total, dialog_progresses, string_progresses)

    CONSOLE.print(table)

def print_strings_console(ui_strings: dict, limit: int = -1) -> None:
    """Renders the parsed UI strings as a Rich table in the terminal."""
    if not ui_strings:
        CONSOLE.print("[yellow]--- Parsed UI Strings (Empty) ---[/yellow]\n")
        return

    table = generate_strings_table(ui_strings, limit)

    CONSOLE.print(table)
    if len(ui_strings) > limit:
        CONSOLE.print(f"[dim]... and {len(ui_strings) - limit} more rows.[/dim]\n")

# --- Generate ---
def generate_dialogue_table(dialogues: dict, limit: int = -1) -> Table:
    """Generates the parsed dialogues as a Rich table."""
    table = Table(title="Parsed Dialogues", show_header=True, header_style="bold magenta")
    table.add_column("Label", style="cyan", no_wrap=True)
    table.add_column("Char", style="green", justify="center")
    table.add_column("Original Text", style="yellow")
    table.add_column("Translated Text", style="blue")

    limit = len(dialogues) if limit == -1 else limit
    for label, data in list(dialogues.items())[:limit]:
        char = data.character if data.character else "-"
        table.add_row(label, char, truncate(data.original, 40), truncate(data.translated, 40))

    return table

def generate_strings_table(ui_strings: dict, limit: int = -1) -> Table:
    """Generates the parsed strings as a Rich table."""
    table = Table(title="Parsed UI Strings", show_header=True, header_style="bold magenta")
    table.add_column("Original String", style="yellow")
    table.add_column("New String", style="blue")

    for old, new in list(ui_strings.items())[:limit]:
        table.add_row(truncate(old, 50), truncate(new, 50))

    return table

def generate_progress_table(file_stats: dict, global_translated: int, global_total: int, dialog_progresses: list, string_progresses: list) -> Table:
    """Generates the progress as a Rich table."""
    table = Table(title="Translation Progress Report", show_header=True, header_style="bold magenta")
    table.add_column("File Name", style="cyan")
    table.add_column("Statistics (Total)", justify="right", style="white")
    table.add_column("Statistics (Dialogues)", justify="right", style="white")
    table.add_column("Statistics (Strings)", justify="right", style="white")
    table.add_column("Progress", justify="right", style="green")

    combined_data = zip(file_stats.items(), dialog_progresses, string_progresses)
    for (filename, (translated, total)), dialog, string in combined_data:
        percent = (translated / total) * 100 if total > 0 else 0
        total_stats_str = f"{translated:>6} / {total:>6}"
        dialogues_stats_str = f"{dialog.translated:>6} / {dialog.total:>6}"
        strings_stats_str = f"{string.translated:>6} / {string.total:>6}"
        pct_str = f"{percent:>6.2f}%"

        pct_color = get_color_gradient(percent)
        table.add_row(filename, total_stats_str, dialogues_stats_str, strings_stats_str, f"[{pct_color}]{pct_str}[/{pct_color}]")
    
    if global_total > 0:
        global_percent = (global_translated / global_total) * 100
        table.add_section()
        table.add_row(
            "[bold]GLOBAL TOTAL[/bold]", 
            f"[bold]{global_translated:>6} / {global_total:>6}[/bold]", 
            f"[bold]-[/bold]", 
            f"[bold]-[/bold]", 
            f"[bold cyan]{global_percent:>6.2f}%[/bold cyan]"
        )

    return table