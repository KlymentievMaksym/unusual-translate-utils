from pathlib import Path

from translate_utils.infrastructure.counter import ProgressCounter
from translate_utils.infrastructure.logger import setup_logging
from translate_utils.infrastructure.path import DEFAULT_DIR_FOR_TRANSLATION
from translate_utils.infrastructure.update_readme_progress import update_readme_progress
from translate_utils.presentation.cli.args import check_translation_progress_parse_args
from translate_utils.presentation.visualize.markdown import ProgressMarkdownReport
from translate_utils.presentation.visualize.mixins import ProgressReportData
from translate_utils.presentation.visualize.terminal import ProgressTerminalReport
from translate_utils.services.progress_service import ProgressService

LOGGER = setup_logging("TranslationProgress")

def check_translation_progress() -> None:
    counter = ProgressCounter()
    progress_checker = ProgressService(counter)
    args = check_translation_progress_parse_args()

    if not args.filepaths:
        paths_to_check = [DEFAULT_DIR_FOR_TRANSLATION]
        LOGGER.info(f"No path provided. Defaulting to: {DEFAULT_DIR_FOR_TRANSLATION}")
    else:
        paths_to_check = [Path(p) for p in args.filepaths]

    translation_stats = progress_checker.get_translation_stats(paths_to_check)

    progress_data = ProgressReportData(translation_stats)
    ProgressTerminalReport(progress_data).display()

    if args.update_readme is not None:
        generated_table = ProgressMarkdownReport(progress_data).generate()
        update_readme_progress(generated_table, Path(args.update_readme))

    if progress_data.translation_stats.global_total.total > 0:
        LOGGER.info(f"GLOBAL DONE: {progress_data.translation_stats.global_total.percentage:>6.2f}% ({progress_data.translation_stats.global_total.translated} / {progress_data.translation_stats.global_total.total})")

if __name__ == "__main__":
    check_translation_progress()
