from collections import defaultdict
from pathlib import Path

from translate_utils.core.entities import FileCheckResult, ReplacementEntity, RuleEntity
from translate_utils.core.interfaces import WriteStrategy
from translate_utils.infrastructure.logging.logger import get_logger
from translate_utils.infrastructure.reporting.formatters import get_underline_char

LOGGER = get_logger(__name__)


class LanguageCheckLogReporter:
    def __init__(self, output_dir: Path, file_writer: WriteStrategy) -> None:
        self._output_dir = output_dir
        self._file_writer = file_writer

        self._next_line = "\n"
        self._global_separator = "=" * 60 + self._next_line
        self._local_separator = "_" * 30 + self._next_line

    def format_file_result(self, file_results: FileCheckResult) -> str:
        text = self._global_separator
        for key, matches in file_results.matches.items():
            if not matches:
                continue

            context_text = matches[0].original_text
            underline_lines: list[str] = []

            replacements: dict[ReplacementEntity, list[str]] = defaultdict(list)
            rules: dict[ReplacementEntity, RuleEntity] = {}

            for match in matches:
                global_offset = match.offset
                flagged_word = context_text[global_offset : global_offset + match.length].lower()
                symbol = get_underline_char(match.issue_type, match.category_id)

                line_chars = list(" " * len(context_text))
                end_offset = min(global_offset + match.length, len(line_chars))
                line_chars[global_offset:end_offset] = symbol * (end_offset - global_offset)

                formatted_line = "".join(line_chars) + f" ({match.issue_type})"
                underline_lines.append(formatted_line)

                replacement_entity = ReplacementEntity(
                    global_offset=global_offset,
                    word=flagged_word,
                )
                rule_entity = RuleEntity(
                    id=match.rule_id,
                    message=match.message,
                )

                replacements[replacement_entity].extend(match.replacements)
                rules[replacement_entity] = rule_entity

            text += f"Key: {key}{self._next_line}"
            text += self._local_separator
            text += context_text + self._next_line
            for line in underline_lines:
                text += line + self._next_line
            text += self._local_separator

            for replacement_entity, replacement in replacements.items():
                rule_entity = rules[replacement_entity]
                repl_str = ", ".join(replacement)
                text += f"Word: {replacement_entity.word}:{replacement_entity.global_offset}"
                text += f"Recomendation: {repl_str}{self._next_line}"
                text += f"Rule id: {rule_entity.id}{self._next_line}"
                text += f"Rule message: {rule_entity.message}{self._next_line}"
                text += self._local_separator

            text += self._next_line + self._global_separator

        return text

    def __call__(self, file_result: FileCheckResult) -> None:
        if not file_result.matches:
            return

        text = self.format_file_result(file_result)
        result_file = file_result.filepath.stem + ".log"
        destination = self._output_dir / result_file

        self._file_writer(filepath=destination, content=text)
        # LOGGER.info(
        #     f"Saved {file_result.filepath} {len(file_result.matches)} results to {result_file}"
        # )
