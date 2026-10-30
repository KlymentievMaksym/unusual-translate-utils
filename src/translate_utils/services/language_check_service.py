import concurrent.futures
from collections import defaultdict
from pathlib import Path

from translate_utils.core.entities import FileCheckResult, LanguageMatch, TranslationsDicts
from translate_utils.core.exceptions import LanguageToolError
from translate_utils.core.interfaces import ParseStrategy, ReadStrategy, TextProcessor
from translate_utils.core.rules import TranslationValidator
from translate_utils.infrastructure.language_tool import LanguageToolClient
from translate_utils.infrastructure.logger import get_logger

LOGGER = get_logger(__name__)


class LanguageCheckService:
    def __init__(
        self,
        file_reader: ReadStrategy[str],
        file_parser: ParseStrategy[TranslationsDicts],
        language_checker: LanguageToolClient,
        validator: TranslationValidator | None = None,
        processor: TextProcessor | None = None,
        item_workers: int = 20,
    ) -> None:
        self.file_reader = file_reader
        self.file_parser = file_parser
        self.language_checker = language_checker
        self.validator = validator
        self.processor = processor
        self.item_workers = item_workers

    def _check_single_item(self, key: str, raw_text: str) -> list[LanguageMatch]:
        clean_text = raw_text
        if self.processor is not None:
            clean_text = self.processor.strip_tags(raw_text)

        if not clean_text.strip():
            return []

        matches: list[LanguageMatch] = []
        try:
            response = self.language_checker.check_text(clean_text)
            for match in response.get("matches", []):
                rule = match.get("rule", {})
                replacements = [
                    r["value"]
                    for r in match.get("replacements", [])
                    if "value" in r
                ]
                context_text = match.get("context", {}).get("text", clean_text)
                matches.append(
                    LanguageMatch(
                        key=key,
                        message=match.get("message", "Style or grammar error"),
                        rule_id=rule.get("id", "UNKNOWN_RULE"),
                        replacements=replacements,
                        context_text=context_text,
                        original_text=clean_text,
                        offset=match.get("offset", 0),
                        length=match.get("length", len(context_text)),
                    )
                )
        except LanguageToolError as exc:
            LOGGER.warning(f"LanguageTool error checking key '{key}': {exc}")
        except Exception as exc:
            LOGGER.error(f"Unexpected error checking key '{key}': {exc}", exc_info=True)

        return matches

    def check_file(self, filepath: Path) -> FileCheckResult:
        content = self.file_reader(filepath)
        parsed_data = self.file_parser(content)
        result = FileCheckResult(filepath=filepath)

        items_to_check: list[tuple[str, str]] = []

        if parsed_data.dialogues:
            for key, dialogue in parsed_data.dialogues.items():
                original = dialogue.original_text
                translation = dialogue.translation_text
                if translation and self.validator and self.validator.check_is_translated(original, translation):
                    items_to_check.append((key, translation))

        if parsed_data.strings:
            for key, string_val in parsed_data.strings.items():
                if string_val and self.validator and self.validator.check_is_translated(key, string_val):
                    items_to_check.append((key, string_val))

        length = len(items_to_check)
        LOGGER.info(f"{length} items to check with {self.item_workers} workers, about {length//self.item_workers} item per worker")

        matches_by_key: defaultdict[str, list[LanguageMatch]] = defaultdict(list)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.item_workers) as executor:
            future_to_key = {
                executor.submit(self._check_single_item, key, text): key
                for key, text in items_to_check
            }
            for future in concurrent.futures.as_completed(future_to_key):
                item_matches = future.result()
                if item_matches:
                    key = future_to_key[future]
                    matches_by_key[key].extend(item_matches)

        result.matches = dict(matches_by_key)

        return result
