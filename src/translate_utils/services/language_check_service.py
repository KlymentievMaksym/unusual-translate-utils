import concurrent.futures
from collections import defaultdict
from pathlib import Path

from rich.progress import Progress as RichProgress
from rich.progress import TaskID

from translate_utils.core.entities import FileCheckResult, LanguageMatch, TranslationsDicts
from translate_utils.core.exceptions import LanguageToolError
from translate_utils.core.interfaces import ParseStrategy, ReadStrategy, TextProcessor
from translate_utils.core.rules import IsSymbolOnlySpec, TranslationValidator
from translate_utils.infrastructure.language_tools.language_tool import LanguageToolClient
from translate_utils.infrastructure.logging.logger import get_logger
from translate_utils.infrastructure.parsing.renpy.processors import RenpyProcessor
from translate_utils.infrastructure.parsing.renpy.regexes import (
    NAME_FORM_MAP,
    RE_NAME_FORM,
    name_form_replacer,
)

LOGGER = get_logger(__name__)


class LanguageCheckService:
    def __init__(
        self,
        file_reader: ReadStrategy[str],
        file_parser: ParseStrategy[TranslationsDicts],
        language_checker: LanguageToolClient,
        validator: TranslationValidator | None = None,
        processor: TextProcessor | None = None,
        dicts: list[str] | None = None,
        item_workers: int = 20,
    ) -> None:
        self._file_reader = file_reader
        self._file_parser = file_parser
        self._language_checker = language_checker
        self._validator = validator
        self._processor = processor
        self._dicts = dicts if dicts is not None else []
        self._item_workers = item_workers

    def _check_single_item(self, key: str, raw_text: str) -> list[LanguageMatch]:
        clean_text = raw_text
        if self._processor is not None:
            clean_text = self._processor.strip_tags(raw_text)

        if not clean_text.strip():
            return []

        clean_text = (
            clean_text.replace("\\n", " ")
            .replace("\\t", " ")
            .replace("[[", "[")
            .replace("[mc]", NAME_FORM_MAP["default"])
        )
        clean_text = RE_NAME_FORM.sub(name_form_replacer, clean_text)

        matches: list[LanguageMatch] = []
        try:
            response = self._language_checker.check_text(clean_text)
            for match in response.get("matches", []):
                offset = match.get("offset", 0)
                length = match.get("length", 0)

                rule = match.get("rule", {})
                rule_id = rule.get("id", "UNKNOWN_RULE")

                context_text = match.get("context", {}).get("text", clean_text)
                flagged_word = context_text[offset : offset + length].lower()

                if flagged_word in self._dicts:
                    continue

                if rule_id == "COMMA_PARENTHESIS_WHITESPACE" and IsSymbolOnlySpec(
                    RenpyProcessor()
                ).is_satisfied_by(flagged_word, ""):
                    continue

                category = rule.get("category", {})
                replacements = [r["value"] for r in match.get("replacements", []) if "value" in r]

                matches.append(
                    LanguageMatch(
                        key=key,
                        message=match.get("message", "Style or grammar error"),
                        rule_id=rule_id,
                        replacements=replacements,
                        context_text=context_text,
                        original_text=clean_text,
                        offset=offset,
                        length=length,
                        issue_type=rule.get("issueType", "uncategorized"),
                        category_id=category.get("id", ""),
                    )
                )
        except LanguageToolError as exc:
            LOGGER.warning(f"LanguageTool error checking key '{key}': {exc}")
        except Exception as exc:
            LOGGER.error(f"Unexpected error checking key '{key}': {exc}", exc_info=True)

        return matches

    def check_file(self, filepath: Path, progress: RichProgress | None = None) -> FileCheckResult:
        content = self._file_reader(filepath)
        parsed_data = self._file_parser(content)
        result = FileCheckResult(filepath=filepath)

        items_to_check: list[tuple[str, str]] = []

        if parsed_data.dialogues:
            for key, dialogue in parsed_data.dialogues.items():
                original = dialogue.original_text
                translation = dialogue.translation_text
                if (
                    translation
                    and self._validator
                    and self._validator.check_is_translated(original, translation)
                ):
                    items_to_check.append((key, translation))

        if parsed_data.strings:
            for key, string_val in parsed_data.strings.items():
                if (
                    string_val
                    and self._validator
                    and self._validator.check_is_translated(key, string_val)
                ):
                    items_to_check.append((key, string_val))

        length = len(items_to_check)
        LOGGER.debug(
            f"{length} items to check with {self._item_workers} workers,"
            f" about {length // self._item_workers} item per worker"
        )

        matches_by_key: defaultdict[str, list[LanguageMatch]] = defaultdict(list)

        file_task: TaskID | None = None
        if progress is not None and items_to_check:
            file_task = progress.add_task(f"[cyan]{filepath.name}", total=len(items_to_check))

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=self._item_workers)
        should_wait = True
        should_cancel_futures = False
        try:
            future_to_key = {
                executor.submit(self._check_single_item, key, text): key
                for key, text in items_to_check[:3]
            }
            for future in concurrent.futures.as_completed(future_to_key):
                item_matches = future.result()
                if item_matches:
                    key = future_to_key[future]
                    matches_by_key[key].extend(item_matches)

                if progress is not None and file_task is not None:
                    progress.advance(file_task)
        except KeyboardInterrupt:
            should_wait = False
            should_cancel_futures = True
            raise
        finally:
            executor.shutdown(wait=should_wait, cancel_futures=should_cancel_futures)

        if progress is not None and file_task is not None:
            progress.remove_task(file_task)

        result.matches = dict(matches_by_key)

        return result
