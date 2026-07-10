import textwrap
from utils.dataclasses import DialogueLine, Progress


def _truncate(text: str | None, max_width: int = 40) -> str:
    """Safely converts text to a single line and truncates it with an ellipsis."""
    if not text:
        return ""
    # Remove newlines so it doesn't break the table height
    clean_text = str(text).replace('\n', ' ').replace('\r', '')
    return textwrap.shorten(clean_text, width=max_width, placeholder="...")

def _print_ascii_table(title: str, headers: list[str], rows: list[list[str]]):
    """Core logic to calculate column widths and draw an ASCII table."""
    if not rows:
        print(f"--- {title} (Empty) ---")
        return

    # Calculate the maximum width for each column (header vs content)
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, col_data in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(col_data)))

    # Build the formatters
    # e.g., "| {0:<15} | {1:<10} |"
    row_format = " | ".join(f"{{:<{w}}}" for w in col_widths)
    row_format = f"| {row_format} |"
    
    # e.g., "+-----------------+------------+"
    separator = "+" + "+".join(f"{'-' * (w + 2)}" for w in col_widths) + "+"

    print(f"\n{title}")
    print(separator)
    print(row_format.format(*headers))
    print(separator)
    for row in rows:
        print(row_format.format(*row))
    print(separator)

def print_dialogue_table(dialogues: dict[str, DialogueLine], limit: int = 15):
    """Prepares the dialogue data and passes it to the table drawer."""
    items_to_show = list(dialogues.items())[:limit]
    
    headers = ["Label", "Char", "Original Text", "Translated Text"]
    rows = []
    
    for label, data in items_to_show:
        rows.append([
            label,
            data.character if data.character else "-",
            _truncate(data.original, max_width=40),
            _truncate(data.translated, max_width=40)
        ])

    _print_ascii_table("Parsed Dialogues", headers, rows)
    
    if len(dialogues) > limit:
        print(f"... and {len(dialogues) - limit} more rows.\n")

def print_ui_strings_table(ui_strings: dict[str, str], limit: int = 15):
    """Prepares the UI string data and passes it to the table drawer."""
    items_to_show = list(ui_strings.items())[:limit]
    
    headers = ["Original String", "New String"]
    rows = []
    
    for old_str, new_str in items_to_show:
        rows.append([
            _truncate(old_str, max_width=50),
            _truncate(new_str, max_width=50)
        ])

    _print_ascii_table("Parsed UI Strings", headers, rows)
    
    if len(ui_strings) > limit:
        print(f"... and {len(ui_strings) - limit} more rows.\n")

def print_progress_table(file_stats: dict[str, tuple[int, int]], global_translated: int, global_total: int, dialog_progresses: list[Progress], string_progresses: list[Progress]):
    """Formats the translation progress stats into an ASCII table."""
    headers = ["File Name", "Trn / Tot (Trn Dial / Tot Dial | Trn Str / Tot Str)", "Progress"]
    rows = []

    for (filename, (translated, total)), dialog_progress, string_progress in zip(sorted(file_stats.items()), dialog_progresses, string_progresses):
        percent = (translated / total) * 100
        rows.append([
            filename,
            f"{translated:>6} / {total:>6} ({dialog_progress.translated:>6} / {dialog_progress.total:>6} | {string_progress.translated:>6} / {string_progress.total:>6})",
            f"{percent:>6.2f}%"
        ])

    rows.append(["-" * 20, "-" * 51, "-" * 8])
    
    if global_total > 0:
        global_percent = (global_translated / global_total) * 100
        rows.append([
            "GLOBAL TOTAL", 
            f"{global_translated:>6} / {global_total:>6}", 
            f"{global_percent:>6.2f}%"
        ])

    _print_ascii_table("Translation Progress Report", headers, rows)