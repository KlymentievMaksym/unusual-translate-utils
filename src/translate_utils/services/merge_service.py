import re
from pathlib import Path

from translate_utils.core.interfaces import ReadStrategy, WriteStrategy
from translate_utils.infrastructure.parsing.renpy.regexes import (
    DLG_HASH,
    DLG_LABEL,
    DLG_TRANSLATED,
    RE_STRINGS_CONFIG,
    RE_TRANSLATE_CONFIG,
    STR_ORIGINAL,
    STR_TRANSLATED,
)
from translate_utils.services.diff_service import ChangeSeverity, DiffResult


class MergeService:
    def __init__(self, file_reader: ReadStrategy[str], file_writer: WriteStrategy[str]) -> None:
        self._file_reader = file_reader
        self._file_writer = file_writer

    def apply_unchanged_translations(
        self, target_filepath: Path, dial_diff: DiffResult, str_diff: DiffResult
    ) -> int:
        if not target_filepath.exists():
            return 0

        file_text = self._file_reader(target_filepath)
        applied_count = 0

        dial_entries = [
            e
            for e in dial_diff.entries
            if e.severity == ChangeSeverity.UNCHANGED and e.old_translation
        ]

        if dial_entries:
            dial_lookup = {e.key: e.old_translation for e in dial_entries}

            def replace_dialogue(match: re.Match[str]) -> str:
                nonlocal applied_count
                data = match.groupdict()
                key = f"{data[DLG_LABEL]}_{data[DLG_HASH]}"

                if key in dial_lookup:
                    old_translation = dial_lookup[key]
                    applied_count += 1

                    start, end = match.span(DLG_TRANSLATED)
                    match_start = match.start()
                    full_match = match.group(0)

                    prefix = full_match[: start - match_start]
                    suffix = full_match[end - match_start :]
                    return f"{prefix}{old_translation}{suffix}"

                return match.group(0)

            file_text = RE_TRANSLATE_CONFIG.pattern.sub(replace_dialogue, file_text)

        str_entries = [
            e
            for e in str_diff.entries
            if e.severity == ChangeSeverity.UNCHANGED and e.old_translation
        ]

        if str_entries:
            str_lookup = {e.key: e.old_translation for e in str_entries}

            def replace_string(match: re.Match[str]) -> str:
                nonlocal applied_count
                data = match.groupdict()
                key = data.get(STR_ORIGINAL)

                if key in str_lookup:
                    old_translation = str_lookup[key]
                    old_translation = old_translation if old_translation is not None else ""
                    applied_count += 1

                    start, end = match.span(STR_TRANSLATED)
                    match_start = match.start()
                    full_match = match.group(0)

                    return (
                        full_match[: start - match_start]
                        + old_translation
                        + full_match[end - match_start :]
                    )

                return match.group(0)

            file_text = RE_STRINGS_CONFIG.pattern.sub(replace_string, file_text)

        if applied_count > 0:
            self._file_writer(filepath=target_filepath, content=file_text)

        return applied_count
