from pathlib import Path

from translate_utils.services.progress_service import ProgressService

from translate_utils.infrastructure.logger import setup_logging
from translate_utils.infrastructure.parser import RpyTranslationParser
from translate_utils.infrastructure.update_readme_progress import update_readme_progress
from translate_utils.infrastructure.path import DEFAULT_DIR_FOR_TRANSLATION

from translate_utils.presentation.cli.args import check_translation_progress_parse_args
from translate_utils.presentation.visualize.terminal import print_progress_console
from translate_utils.presentation.visualize.markdown import generate_progress_markdown

LOGGER = setup_logging("TranslationProgress")

def check_translation_progress():
    parser = RpyTranslationParser()
    progress_checker = ProgressService(parser)
    args = check_translation_progress_parse_args()

    if not args.filepaths:
        paths_to_check = [DEFAULT_DIR_FOR_TRANSLATION]
        LOGGER.info(f"No path provided. Defaulting to: {DEFAULT_DIR_FOR_TRANSLATION}")
    else:
        paths_to_check = [Path(p) for p in args.filepaths]

    raw_data = progress_checker.get_raw_translation_data(paths_to_check)
    if raw_data is None:
        return

    file_stats, global_translated, global_total, dialog_progresses, string_progresses = raw_data

    print_progress_console(file_stats, global_translated, global_total, dialog_progresses, string_progresses)
    if args.update_readme is not None:
        generated_table = generate_progress_markdown(file_stats, global_translated, global_total, dialog_progresses, string_progresses)
        update_readme_progress(generated_table, Path(args.update_readme))

    if global_total > 0:
        global_percent = (global_translated / global_total) * 100
        LOGGER.info(f"GLOBAL DONE: {global_percent:>6.2f}% ({global_translated} / {global_total})")

if __name__ == "__main__":
    check_translation_progress()
