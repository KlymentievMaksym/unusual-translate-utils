from tabulate import tabulate

from translate_utils.utils.visualize.utils import truncate


def generate_dialogue_markdown(dialogues: dict, limit: int = 15) -> str:
    """Generates a Markdown table string for parsed dialogues."""
    if not dialogues:
        return "*(No dialogues parsed)*\n"

    headers = ["Label", "Char", "Original Text", "Translated Text"]
    rows = [
        [
            label, 
            data.character if data.character else "-", 
            truncate(data.original, 40), 
            truncate(data.translated, 40)
        ] 
        for label, data in list(dialogues.items())[:limit]
    ]
    return tabulate(rows, headers=headers, tablefmt="github")

def generate_strings_markdown(ui_strings: dict, limit: int = 15) -> str:
    """Generates a Markdown table string for parsed UI strings."""
    if not ui_strings:
        return "*(No UI strings parsed)*\n"

    headers = ["Original String", "New String"]
    rows = [
        [truncate(old, 50), truncate(new, 50)] 
        for old, new in list(ui_strings.items())[:limit]
    ]
    return tabulate(rows, headers=headers, tablefmt="github")

def generate_progress_markdown(file_stats: dict, global_translated: int, global_total: int, dialog_progresses: list, string_progresses: list) -> str:
    """Generates a Markdown table string for translation progress."""
    if not file_stats:
        return "*(No progress data available)*\n"

    headers = ["File Name", "Statistics (Total)", "Statistics (Dialogues)", "Statistics (Strings)", "Progress"]
    rows = []

    combined_data = zip(file_stats.items(), dialog_progresses, string_progresses)
    for (filename, (translated, total)), dialog, string in combined_data:
        percent = (translated / total) * 100 if total > 0 else 0

        total_stats_str = f"{translated:>6} / {total:>6}"
        dialogues_stats_str = f"{dialog.translated:>6} / {dialog.total:>6}"
        strings_stats_str = f"{string.translated:>6} / {string.total:>6}"

        rows.append([filename, total_stats_str, dialogues_stats_str, strings_stats_str, f"{percent:.2f}%"])
    
    if global_total > 0:
        global_percent = (global_translated / global_total) * 100
        rows.append(["**GLOBAL TOTAL**", f"**{global_translated} / {global_total}**", f"**-**", f"**-**", f"**{global_percent:.2f}%**"])

    return tabulate(rows, headers=headers, tablefmt="github", colalign=("left", "right", "right", "right", "right"))
