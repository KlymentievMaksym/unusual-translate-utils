from pathlib import Path

from utils.logger import setup_logging
from utils.parser import cleanup_repeats_parse_args, RpyTranslationParser
from utils.visualize import print_dialogue_table
from utils.cleaner import process_cleaned_lines
from utils.saver import save_lines_to_file


LOGGER = setup_logging("CleanupRepeats")

def cleanup_repeats():
    parser = RpyTranslationParser()
    args = cleanup_repeats_parse_args()

    if args.filepaths is None:
        LOGGER.info("There is no filepath given")
    else:
        LOGGER.info(f"Loading and parsing: {args.filepaths}...")
        for filepath in args.filepaths:
            filepath = Path(filepath)
            if not filepath.exists():
                LOGGER.warning(f"Filepath {filepath.absolute()} is not exists")

            dialogues = parser.parse_dialogues_only(filepath)

            LOGGER.info(f"Lengths: scripts {len(dialogues)}")

            print_dialogue_table(dialogues, limit=3)

            output_lines, replaced_count = process_cleaned_lines(filepath, dialogues)
            LOGGER.info(f"Replaced {replaced_count} duplicate strings.")

            out_filepath = save_lines_to_file(original_filepath=filepath, output_lines=output_lines, new_name=args.name)
            LOGGER.info(f"Saved cleaned file to: {out_filepath}")

if __name__ == "__main__":
    cleanup_repeats()