from pathlib import Path

from translate_utils.core.cleaner import TranslationCleaner
from translate_utils.core.replacer_methods import CleanStrategy
from translate_utils.infrastructure.parser import RpyTranslationParser
from translate_utils.infrastructure.saver import save_lines_to_file
from translate_utils.infrastructure.logger import get_logger

LOGGER = get_logger(__name__)

class CleanupService:
    def __init__(self, parser: RpyTranslationParser) -> None:
        self.parser = parser

    def clean_and_save(self, filepath: str | Path, new_name: str | Path | None, clean_method: CleanStrategy) -> None:
        filepath = Path(filepath)
        if not filepath.exists():
            LOGGER.warning(f"Filepath {filepath.absolute()} is not exists")
            return
        file_text = self.parser.read_file(filepath)

        new_filepath = new_name
        if new_name is not None:
            new_filepath = Path(new_name)
            if new_filepath.exists():
                LOGGER.warning(f"Filepath {new_filepath.absolute()} is exists")

        dialogues = self.parser.parse_dialogues_only(filepath)
        LOGGER.info(f"Scripts length is {len(dialogues)}")
        # print_dialogue_console(dialogues, limit=5)

        cleaner = TranslationCleaner(dialogues, clean_method)

        text_to_replace_with, replaced_count = cleaner.clean(file_text)
        LOGGER.info(f"Replaced {replaced_count} duplicate strings.")

        out_filepath = save_lines_to_file(original_filepath=filepath, text_to_replace_with=text_to_replace_with, new_name=new_filepath)
        LOGGER.info(f"Saved cleaned file to: {out_filepath}")
