import re
from typing import Mapping, Sequence

from translate_utils.core.entities import CleanResults
from translate_utils.core.interfaces import CleanStrategy, MatchExtractorFunc


class TranslationCleaner:
    def __init__(self, pattern: re.Pattern[str], extractor: MatchExtractorFunc):

        self._pattern = pattern
        self._extractor = extractor

    def clean(
        self,
        file_text: str,
        text_to_position: Mapping[str, Sequence[str]],
        clean_method: CleanStrategy,
    ) -> CleanResults:

        replaced_count = 0

        def replacer(match: re.Match[str]) -> str:
            nonlocal replaced_count

            extracted_params = self._extractor(match)

            if extracted_params.original_text in text_to_position:
                replaced_count += 1
                script_pos_str = ", ".join(text_to_position[extracted_params.original_text])

                return clean_method(
                    extracted_params.full_text, extracted_params.indent, script_pos_str
                )

            return extracted_params.full_text

        cleaned_text = self._pattern.sub(replacer, file_text)

        return CleanResults(cleaned_text, replaced_count)
