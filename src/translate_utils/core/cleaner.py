import re

from translate_utils.core.replacer_methods import CleanStrategy
from translate_utils.core.entities import DialogueLine
from translate_utils.core.regexes import RE_STRINGS_BLOCK

class TranslationCleaner:
    def __init__(self, dialogues: dict[str, DialogueLine], clean_method: CleanStrategy):
        self.text_to_pos = self._build_reverse_lookup(dialogues)
        self.clean_method = clean_method

    def _build_reverse_lookup(self, dialogues: dict[str, DialogueLine]) -> dict[str, list[str]]:
        text_to_pos: dict[str, list[str]] = {}
        for data in dialogues.values():
            if data.original and data.script_pos:
                if data.original not in text_to_pos:
                    text_to_pos[data.original] = []
                text_to_pos[data.original].append(data.script_pos)
        return text_to_pos

    def clean(self, file_text: str) -> tuple[str, int]:
        self.replaced_count = 0

        cleaned_text = RE_STRINGS_BLOCK.sub(self._replacer, file_text)

        return cleaned_text, self.replaced_count
    
    def _replacer(self, match: re.Match) -> str:
        text = match.group(0)
        indent = match.group(1)
        old_text = match.group(3)

        if old_text in self.text_to_pos:
            self.replaced_count += 1
            script_pos_str = ", ".join(self.text_to_pos[old_text])

            return self.clean_method(text, indent, script_pos_str)
        return text
