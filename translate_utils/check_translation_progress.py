from pathlib import Path

from utils.logger import setup_logging
from utils.parser import check_translation_progress_parse_args, RpyTranslationParser
from utils.visualize import print_progress_table
from utils.dataclasses import Progress


LOGGER = setup_logging("TranslationProgress")


def calculate_file_progress(filepath: Path, parser: RpyTranslationParser) -> tuple[int, int, Progress, Progress]:
    """
    Parses a single file and returns (translated_count, total_count).
    """
    dialogues, ui_strings = parser.parse_all(filepath)
    dialog_length = len(dialogues)
    string_length = len(ui_strings)

    total = dialog_length + string_length

    dialog_translated = 0
    string_translated = 0
    for label, dialog in dialogues.items():
        if dialog.original != dialog.translated and not dialog.translated.isascii():
            dialog_translated += 1
    for old, new in ui_strings.items():
        if old != new and not new.isascii():
            string_translated += 1

    translated = dialog_translated + string_translated

    return translated, total, Progress(dialog_translated, dialog_length), Progress(string_translated, string_length)

def check_translation_progress():
    parser = RpyTranslationParser()
    args = check_translation_progress_parse_args()

    if not args.filepaths:
        default_dir = Path(__file__).parent.parent / "game" / "tl" / "ukrainian"
        paths_to_check = [default_dir]
        LOGGER.info(f"No path provided. Defaulting to: {default_dir}")
    else:
        paths_to_check = [Path(p) for p in args.filepaths]

    file_stats: dict[str, tuple[int, int]] = {}
    global_translated = 0
    global_total = 0

    rpy_files: list[Path] = []
    for target_path in paths_to_check:
        if not target_path.exists():
            LOGGER.error(f"Path does not exist: {target_path.absolute()}")
            continue
            
        if target_path.is_file() and target_path.suffix == ".rpy":
            rpy_files.append(target_path)
        elif target_path.is_dir():
            rpy_files.extend(target_path.rglob("*.rpy"))
    # print(rpy_files)

    if not rpy_files:
        LOGGER.warning("No .rpy files found to process.")
        return

    LOGGER.info(f"Found {len(rpy_files)} files. Calculating progress...")
    dialog_progresses = []
    string_progresses = []
    for filepath in rpy_files:
        translated, total, dialog_progress, string_progress = calculate_file_progress(filepath, parser)
        dialog_progresses.append(dialog_progress)
        string_progresses.append(string_progress)

        if total > 0:
            file_stats[filepath.name] = (translated, total)
            global_translated += translated
            global_total += total

    # for filename, (translated, total) in file_stats.items():
    #     percent = (translated / total) * 100
    #     LOGGER.info(f"Done: {percent:>6.2f}% | File: {filename}")

    print_progress_table(file_stats, global_translated, global_total, dialog_progresses, string_progresses)
    if global_total > 0:
        global_percent = (global_translated / global_total) * 100
        LOGGER.info(f"GLOBAL DONE: {global_percent:>6.2f}% ({global_translated} / {global_total})")

if __name__ == "__main__":
    check_translation_progress()
