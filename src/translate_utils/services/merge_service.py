import re
from pathlib import Path

from translate_utils.core.interfaces import ReadStrategy, WriteStrategy
from translate_utils.infrastructure.parsers.regexes import RE_STRINGS_CONFIG, RE_TRANSLATE_CONFIG
from translate_utils.services.diff_service import ChangeSeverity, DiffResult


class MergeService:
    def __init__(
        self,
        file_reader: ReadStrategy[str],
        file_writer: WriteStrategy[str]
    ) -> None:
        self._file_reader = file_reader
        self._file_writer = file_writer

    def apply_unchanged_translations(
        self, target_filepath: Path, dial_diff: DiffResult, str_diff: DiffResult
    ) -> int:
        """
        Reads the target file, replaces the empty translation lines with the
        old translations for UNCHANGED dialogues and unchanged string keys.
        Returns the total number of translations applied.
        """
        if not target_filepath.exists():
            return 0

        file_text = self._file_reader(target_filepath)
        applied_count = 0

        # ==========================================
        # 1. PROCESS DIALOGUES
        # ==========================================
        dial_entries = [
            e for e in dial_diff.entries
            if e.severity == ChangeSeverity.UNCHANGED and getattr(e, 'old_translation', None)
        ]

        if dial_entries:
            dial_lookup = {e.key: e.old_translation for e in dial_entries}

            def replace_dialogue(match: re.Match) -> str:
                nonlocal applied_count
                data = match.groupdict()
                key = f"{data['script_label']}_{data['script_hash']}"

                if key in dial_lookup:
                    old_translation = dial_lookup[key]
                    full_match = match.group(0)

                    # Split exactly at the last two quotes to inject the translation
                    parts = full_match.rsplit('"', 2)
                    if len(parts) == 3:
                        applied_count += 1
                        return f'{parts[0]}"{old_translation}"{parts[2]}'

                return match.group(0)

            file_text = RE_TRANSLATE_CONFIG.pattern.sub(replace_dialogue, file_text)

        # ==========================================
        # 2. PROCESS STRINGS
        # ==========================================
        # For strings, if the English key is still there (UNCHANGED, MINOR, MAJOR),
        # and the old text was actually translated (doesn't equal the English key), we bring it over.
        valid_str_severities = {ChangeSeverity.UNCHANGED, ChangeSeverity.MINOR, ChangeSeverity.MAJOR}
        str_entries = [
            e for e in str_diff.entries
            if e.severity in valid_str_severities and e.old_text and e.old_text != e.key
        ]

        if str_entries:
            str_lookup = {e.key: e.old_text for e in str_entries}

            def replace_string(match: re.Match) -> str:
                nonlocal applied_count
                data = match.groupdict()
                # For UI strings, the original English text is our unique key
                key = data.get('old_text')

                if key in str_lookup:
                    old_translation = str_lookup[key]
                    full_match = match.group(0)

                    # The translation is in the 'new "..."' block at the end of the match
                    parts = full_match.rsplit('"', 2)
                    if len(parts) == 3:
                        applied_count += 1
                        return f'{parts[0]}"{old_translation}"{parts[2]}'

                return match.group(0)

            file_text = RE_STRINGS_CONFIG.pattern.sub(replace_string, file_text)

        # ==========================================
        # WRITE RESULT
        # ==========================================
        if applied_count > 0:
            self._file_writer(filepath=target_filepath, content=file_text)

        return applied_count
