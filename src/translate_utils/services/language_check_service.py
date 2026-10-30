import concurrent.futures
from pathlib import Path

from translate_utils.core.entities import FileCheckResult, LanguageMatch, TranslationsDicts
from translate_utils.core.interfaces import ParseStrategy, ReadStrategy, TextProcessor
from translate_utils.infrastructure.language_tool import LanguageToolClient
from translate_utils.infrastructure.logger import get_logger

LOGGER = get_logger(__name__)


class LanguageCheckService:
    def __init__(
        self,
        file_reader: ReadStrategy[str],
        file_parser: ParseStrategy[TranslationsDicts],
        language_checker: LanguageToolClient,
        processor: TextProcessor | None = None,
        item_workers: int = 20,
    ) -> None:
        self.file_reader = file_reader
        self.file_parser = file_parser
        self.language_checker = language_checker
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
                matches.append(
                    LanguageMatch(
                        key=key,
                        message=match.get("message", "Style or grammar error"),
                        rule_id=rule.get("id", "UNKNOWN_RULE"),
                        replacements=replacements[:5],
                        context_text=match.get("context", {}).get("text", clean_text),
                    )
                )
        except Exception:
            pass
        return matches

    def check_file(self, filepath: Path) -> FileCheckResult:
        content = self.file_reader(filepath)
        parsed_data = self.file_parser(content)
        result = FileCheckResult(filepath=filepath)

        items_to_check: list[tuple[str, str]] = []

        if parsed_data.dialogues:
            for key, dialogue in parsed_data.dialogues.items():
                text = dialogue.translation_text or dialogue.original_text
                if text:
                    items_to_check.append((key, text))

        if parsed_data.strings:
            for key, string_val in parsed_data.strings.items():
                if string_val:
                    items_to_check.append((key, string_val))

        LOGGER.info(f"Items to check: {len(items_to_check)}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.item_workers) as executor:
            futures = [
                executor.submit(self._check_single_item, key, text)
                for key, text in items_to_check
            ]
            for future in concurrent.futures.as_completed(futures):
                result.matches.extend(future.result())

        return result
