import re
from collections import defaultdict
from typing import Mapping, Sequence, Callable

from translate_utils.core.replacer_methods import CleanStrategy
from translate_utils.core.entities import DialogueLine
MatchExtractor = Callable[[re.Match[str]], tuple[str, str, str]]

def strings_block_extractor(match: re.Match[str]) -> tuple[str, str, str]:
    """
    Specific strategy for RE_STRINGS_BLOCK.
    Knows exactly how to parse the strings block match.
    """
    return match.group(0), match.group("indent"), match.group("old_text")

def translate_block_extractor(match: re.Match[str]) -> tuple[str, str, str]:
    """
    Specific strategy for RE_TRANSLATE_BLOCK.
    (Example of how you can reuse the cleaner for different blocks).
    """
    return match.group(0), "\t", match.group("original_text")

class TranslationCleaner:
    def __init__(self, dialogues: dict[str, DialogueLine], clean_method: CleanStrategy, pattern: re.Pattern[str], extractor: MatchExtractor):
        self.text_to_position = self._build_reverse_lookup(dialogues)
        self.clean_method = clean_method
        self.pattern = pattern
        self.extractor = extractor

    def _build_reverse_lookup(self, dialogues: dict[str, DialogueLine]) -> Mapping[str, Sequence[str]]:
        lookup: defaultdict[str, list[str]] = defaultdict(list)
        
        for data in dialogues.values():
            if data.original_text and data.script_position:
                lookup[data.original_text].append(data.script_position)

        return {
            text: tuple(positions) 
            for text, positions in lookup.items()
        }

    def clean(self, file_text: str) -> tuple[str, int]:
        replaced_count = 0

        def replacer(match: re.Match) -> str:
            nonlocal replaced_count

            text, indent, old_text = self.extractor(match)

            if old_text in self.text_to_position:
                replaced_count += 1
                script_pos_str = ", ".join(self.text_to_position[old_text])

                return self.clean_method(text, indent, script_pos_str)
            
            return text

        cleaned_text = self.pattern.sub(replacer, file_text)

        return cleaned_text, replaced_count
