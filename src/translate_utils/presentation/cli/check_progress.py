from pathlib import Path

from translate_utils.services.progress_service import ProgressService

from translate_utils.infrastructure.logger import setup_logging
from translate_utils.infrastructure.parser import RpyTranslationParser
from translate_utils.infrastructure.update_readme_progress import update_readme_progress
from translate_utils.infrastructure.path import DEFAULT_DIR_FOR_TRANSLATION

from translate_utils.presentation.cli.args import check_translation_progress_parse_args
from translate_utils.presentation.visualize.mixins import ProgressReportData
from translate_utils.presentation.visualize.terminal import ProgressTerminalReport
from translate_utils.presentation.visualize.markdown import ProgressMarkdownReport

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

    progress_data = ProgressReportData(file_stats, global_translated, global_total, dialog_progresses, string_progresses)
    ProgressTerminalReport(progress_data).display()

    if args.update_readme is not None:
        generated_table = ProgressMarkdownReport(progress_data).generate()
        update_readme_progress(generated_table, Path(args.update_readme))

    if global_total > 0:
        LOGGER.info(f"GLOBAL DONE: {progress_data.global_percent:>6.2f}% ({global_translated} / {global_total})")

if __name__ == "__main__":
    check_translation_progress()
