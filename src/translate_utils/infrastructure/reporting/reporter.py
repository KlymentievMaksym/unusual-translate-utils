from collections import defaultdict
from pathlib import Path

from translate_utils.core.entities import FileCheckResult, ReplacementEntity, RuleEntity
from translate_utils.infrastructure.filesystem.io import write_renpy_file
from translate_utils.infrastructure.logging.logger import get_logger

LOGGER = get_logger(__name__)


class LanguageCheckLogReporter:
    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir

    def format_file_result(self, file_results: FileCheckResult) -> str:
        next_line = "\n"
        global_separator = "=" * 60 + next_line
        local_separator = "_" * 30 + next_line

        text = global_separator
        for key, matches in file_results.matches.items():
            if not matches:
                continue

            context_text = matches[0].original_text
            underliner = list(" " * len(context_text))

            replacements: dict[ReplacementEntity, list[str]] = defaultdict(list)
            rules: dict[ReplacementEntity, RuleEntity] = {}

            for match in matches:
                global_offset = match.offset
                flagged_word = context_text[global_offset : global_offset + match.length].lower()

                replacement_entity = ReplacementEntity(
                    global_offset=global_offset,
                    word=flagged_word,
                )
                rule_entity = RuleEntity(
                    id=match.rule_id,
                    message=match.message,
                )

                underliner[global_offset : global_offset + match.length] = "-" * match.length
                replacements[replacement_entity].extend(match.replacements)
                rules[replacement_entity] = rule_entity

            text += f"Key: {key}{next_line}"
            text += local_separator
            text += context_text + next_line
            text += "".join(underliner) + next_line
            text += local_separator

            for replacement_entity, replacement in replacements.items():
                rule_entity = rules[replacement_entity]
                repl_str = ", ".join(replacement)
                text += f"Word: {replacement_entity.word}:{replacement_entity.global_offset}"
                text += f"Recomendation: {repl_str}{next_line}"
                text += f"Rule id: {rule_entity.id}{next_line}"
                text += f"Rule message: {rule_entity.message}{next_line}"
                text += local_separator

            text += next_line + global_separator

        return text

    def write_single_file_log(self, file_result: FileCheckResult) -> None:
        if not file_result.matches:
            return

        text = self.format_file_result(file_result)
        result_file = Path(file_result.filepath).stem + ".log"
        destination = self._output_dir / result_file

        write_renpy_file(destination, text)
        LOGGER.info(f"Saved {file_result.filepath} results to {result_file}")
