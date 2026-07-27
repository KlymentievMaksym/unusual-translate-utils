import re

from translate_utils.core.entities import ExtractorParams


def strings_block_extractor(match: re.Match[str]) -> ExtractorParams:
    """
    Specific strategy for RE_STRINGS_BLOCK.
    Knows exactly how to parse the strings block match.
    """
    return ExtractorParams(match.group(0), match.group("indent"), match.group("old_text"))


def translate_block_extractor(match: re.Match[str]) -> ExtractorParams:
    """
    Specific strategy for RE_TRANSLATE_BLOCK.
    (Example of how you can reuse the cleaner for different blocks).
    """
    return ExtractorParams(match.group(0), "\t", match.group("original_text"))
