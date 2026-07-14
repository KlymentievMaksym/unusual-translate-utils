from pathlib import Path

from translate_utils.core.entities import Progress
from translate_utils.infrastructure.parser import RpyTranslationParser
from translate_utils.infrastructure.logger import get_logger

LOGGER = get_logger(__name__)

class ProgressService:
    def __init__(self, parser: RpyTranslationParser) -> None:
        self.parser = parser

    def calculate_file_progress(self, filepath: Path) -> tuple[int, int, Progress, Progress]:
        """
        Parses a single file and returns (translated_count, total_count).
        """
        dialogues, ui_strings = self.parser.parse_all(filepath)
        dialog_length = len(dialogues)
        string_length = len(ui_strings)

        total = dialog_length + string_length

        dialog_translated = 0
        string_translated = 0
        for label, dialog in dialogues.items():
            if dialog.is_translated():
                dialog_translated += 1
        for old, new in ui_strings.items():
            if old != new and not new.isascii():
                string_translated += 1

        translated = dialog_translated + string_translated

        return translated, total, Progress(dialog_translated, dialog_length), Progress(string_translated, string_length)

    def get_raw_translation_data(self, paths_to_check: list[Path]) -> (tuple[dict[str, tuple[int, int]], int, int, list[Progress], list[Progress]] | None):
        file_stats: dict[str, tuple[int, int]] = {}
        global_translated = 0
        global_total = 0
        dialog_progresses: list[Progress] = []
        string_progresses: list[Progress] = []
        
        rpy_files = []
        for target_path in paths_to_check:
            if target_path.is_file() and target_path.suffix == ".rpy":
                rpy_files.append(target_path)
            elif target_path.is_dir():
                rpy_files.extend(target_path.rglob("*.rpy"))

        if not rpy_files:
            LOGGER.warning("No .rpy files found to process.")
            return
        LOGGER.info(f"Found {len(rpy_files)} files. Calculating progress...")

        rpy_files.sort(key=lambda path: path.name)

        for filepath in rpy_files:
            translated, total, dialog_progress, string_progress = self.calculate_file_progress(filepath)
            if total > 0:
                dialog_progresses.append(dialog_progress)
                string_progresses.append(string_progress)
                file_stats[filepath.name] = (translated, total)
                global_translated += translated
                global_total += total
                
        return file_stats, global_translated, global_total, dialog_progresses, string_progresses