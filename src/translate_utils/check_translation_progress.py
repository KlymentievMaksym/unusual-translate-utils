from pathlib import Path

from translate_utils.utils.logger import setup_logging
from translate_utils.utils.parser import check_translation_progress_parse_args, get_raw_translation_data
from translate_utils.utils.visualize.terminal import print_progress_console
from translate_utils.utils.visualize.markdown import generate_progress_markdown
from translate_utils.utils.update_readme_progress import update_readme_progress


LOGGER = setup_logging("TranslationProgress")

def check_translation_progress():
    args = check_translation_progress_parse_args()

    if not args.filepaths:
        default_dir = Path(__file__).parents[2] / "game" / "tl" / "ukrainian"
        paths_to_check = [default_dir]
        LOGGER.info(f"No path provided. Defaulting to: {default_dir}")
    else:
        paths_to_check = [Path(p) for p in args.filepaths]

    file_stats, global_translated, global_total, dialog_progresses, string_progresses = get_raw_translation_data(paths_to_check)

    # if not rpy_files:
    #     LOGGER.warning("No .rpy files found to process.")
    #     return

    # LOGGER.info(f"Found {len(rpy_files)} files. Calculating progress...")

    print_progress_console(file_stats, global_translated, global_total, dialog_progresses, string_progresses)
    if args.update_readme is not None:
        generated_table = generate_progress_markdown(file_stats, global_translated, global_total, dialog_progresses, string_progresses)
        update_readme_progress(generated_table, Path(args.update_readme))

    if global_total > 0:
        global_percent = (global_translated / global_total) * 100
        LOGGER.info(f"GLOBAL DONE: {global_percent:>6.2f}% ({global_translated} / {global_total})")

if __name__ == "__main__":
    check_translation_progress()
