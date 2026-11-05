from pathlib import Path

from translate_utils.core.exceptions import FileError
from translate_utils.core.interfaces import CleanStrategy
from translate_utils.core.replacer_methods import AVAILABLE_METHODS, CleanMethod
from translate_utils.infrastructure.factories import create_default_cleaner, create_default_parser
from translate_utils.infrastructure.io import read_renpy_file, write_renpy_file
from translate_utils.infrastructure.logger import setup_logging
from translate_utils.infrastructure.parser import RegexDialogueParser
from translate_utils.infrastructure.parsers.regexes import RE_TRANSLATE_CONFIG
from translate_utils.infrastructure.path import DEFAULT_DIR_FOR_COMPARE_LOGS
from translate_utils.presentation.cli.args import compare_dirs_parse_args
from translate_utils.services.cleanup_service import CleanupService
from translate_utils.services.compare_service import CompareService
from translate_utils.services.diff_service import ChangeEntry, DialogueSequenceDiff, StringDiff
from translate_utils.services.mappers import build_reverse_lookup
from translate_utils.services.merge_service import MergeService

LOGGER = setup_logging("CompareDirs")


def compare_dirs() -> None:
    LOGGER.info("Starting compare process...")
    args = compare_dirs_parse_args()
    if not args.is_suitable_clean_method():
        available_methods_str = ", ".join(AVAILABLE_METHODS)
        LOGGER.warning(
            f"Clean method '{args.clean_method}' is not supported. "
            f"Available methods: [{available_methods_str}]. "
            f"Defaulting to '{CleanMethod.ONLY_COMMENT}'..."
        )

    clean_method: CleanStrategy = AVAILABLE_METHODS.get(
        args.clean_method, AVAILABLE_METHODS[CleanMethod.ONLY_COMMENT]
    )

    LOGGER.info(f"Loading and comparing: {args.dirs}...")
    dir1, dir2 = args.dirs
    _compare_dirs(
        dir1=dir1,
        dir2=dir2,
        clean_method=clean_method,
        minor_threshold=args.minor_threshold,
        match_threshold=args.match_threshold,
        auto=args.auto,
    )


def _compare_dirs(
    dir1: str,
    dir2: str,
    clean_method: CleanStrategy,
    minor_threshold: float,
    match_threshold: float,
    auto: bool = False,
) -> None:
    cleaner = create_default_cleaner()
    parser = create_default_parser()

    clean_service = CleanupService(
        file_reader=read_renpy_file,
        file_parser=RegexDialogueParser(RE_TRANSLATE_CONFIG),
        file_cleaner=cleaner,
        file_writer=lambda filepath, content: None,
        mapper=build_reverse_lookup,
        verbose=False,
    )
    compare_service = CompareService(
        file_reader=read_renpy_file, file_parser=parser, file_cleaner=cleaner
    )
    if auto:
        merge_service = MergeService(file_reader=read_renpy_file, file_writer=write_renpy_file)

    compare_results = compare_service.compare_directories(dir1, dir2)
    text = f"""
Added: {compare_results.added}
Deleted: {compare_results.deleted}
Identical: {compare_results.identical}
Changed: {compare_results.changed}
"""
    result_file = "_GLOBAL.log"
    write_renpy_file(DEFAULT_DIR_FOR_COMPARE_LOGS / result_file, text)
    LOGGER.info(f"Saved global results to {result_file}")

    for filepath in compare_results.changed:
        LOGGER.info(f"Comparing {filepath}...")
        text = f"Changed: {filepath}"
        try:
            clean_results1 = clean_service.clean(
                filepath=Path(dir1) / filepath, clean_method=clean_method
            )
            clean_results2 = clean_service.clean(
                filepath=Path(dir2) / filepath, clean_method=clean_method
            )
            dial_and_str1 = parser(clean_results1.cleaned_text)
            dial_and_str2 = parser(clean_results2.cleaned_text)

            string_diff = StringDiff(
                min_match_threshold=match_threshold, minor_threshold=minor_threshold
            )
            dialogue_diff = DialogueSequenceDiff(
                min_match_threshold=match_threshold, minor_threshold=minor_threshold
            )

            old_dialogues = list(dial_and_str1.dialogues.values())
            new_dialogues = list(dial_and_str2.dialogues.values())

            dial_diff = dialogue_diff.compare(old_dialogues, new_dialogues)
            str_diff = string_diff.compare(dial_and_str1.strings, dial_and_str2.strings)

            if auto:
                target_path = Path(dir2) / filepath
                applied_count = merge_service.apply_unchanged_translations(
                    target_path, dial_diff, str_diff
                )
                if applied_count > 0:
                    LOGGER.info(f"Successfully applied {applied_count} translations to {filepath}")

            # render_diff(filepath, dial_diff, str_diff)

            attrs = ["major", "minor", "added", "removed"]
            show_similarity_in = attrs[:2]

            attrs_sep = "____________________________"
            res_attrs_sep = "----------------------------"

            for attr in attrs:
                text += (
                    f"\n{attrs_sep}\n{attr.capitalize()} changes: "
                    f"{len(getattr(dial_diff, attr)) + len(getattr(str_diff, attr))}"
                )

                dialogues_changes: list[ChangeEntry] = getattr(dial_diff, attr)
                strings_changes: list[ChangeEntry] = getattr(str_diff, attr)

                d_result = "\n".join(
                    [
                        (
                            f"\n\tKey: {dialogue.key}"
                            + (
                                f"\n\tSimilarity: {dialogue.similarity:.2f}%"
                                if attr in show_similarity_in
                                else ""
                            )
                            + f"\n\tOld translation: {dialogue.old_translation}"
                            f"\n\tOld text: {dialogue.old_text}"
                            f"\n\tNew text: {dialogue.new_text}"
                        )
                        for dialogue in dialogues_changes
                    ]
                )
                s_result = "\n".join(
                    [
                        (
                            f"\n\tKey: {string.key}"
                            + (
                                f"\n\tSimilarity: {string.similarity:.2f}%"
                                if attr in show_similarity_in
                                else ""
                            )
                            + f"\n\tOld text: {string.old_text}"
                            f"\n\tNew text: {string.new_text}"
                        )
                        for string in strings_changes
                    ]
                )

                text += f"\n{res_attrs_sep}\n{attr.capitalize()} dialogues changes: {d_result}"
                text += f"\n{res_attrs_sep}\n{attr.capitalize()} strings changes: {s_result}"

        except FileError as e:
            LOGGER.error(f"Skipped {filepath} due to file error: {e}")
        except Exception as e:
            LOGGER.critical(f"Unexpected fatal error processing {filepath}: {e}", exc_info=True)
        result_file = Path(filepath).stem + ".log"
        write_renpy_file(DEFAULT_DIR_FOR_COMPARE_LOGS / result_file, text)
        LOGGER.info(f"Saved results to {result_file}")


if __name__ == "__main__":
    compare_dirs()
