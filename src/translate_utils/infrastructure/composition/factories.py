from translate_utils.core.cleaner import TranslationCleaner
from translate_utils.core.rules import (
    HasTargetAlphabetSpec,
    # NoMixedAlphabetsSpec,  # commented for being too strict
    IsDifferentSpec,
    # IsNotEmptySpec,  # commented for being too strict
    IsSymbolOnlySpec,
    TranslationValidator,
)
from translate_utils.infrastructure.parsing.renpy.extractors import strings_block_extractor
from translate_utils.infrastructure.parsing.renpy.parser import (
    RegexDialAndStrParser,
    RegexDialogueParser,
    RegexStringParser,
)
from translate_utils.infrastructure.parsing.renpy.processors import RenpyProcessor
from translate_utils.infrastructure.parsing.renpy.regexes import (
    RE_STRINGS_CONFIG,
    RE_TRANSLATE_CONFIG,
)
from translate_utils.infrastructure.progress.counter import RegexProgressCounter


def create_default_cleaner() -> TranslationCleaner:
    return TranslationCleaner(RE_STRINGS_CONFIG.pattern, strings_block_extractor)


def create_default_parser() -> RegexDialAndStrParser:
    return RegexDialAndStrParser(
        dialogue_parser=RegexDialogueParser(RE_TRANSLATE_CONFIG),
        string_parser=RegexStringParser(RE_STRINGS_CONFIG),
    )


def create_default_validator() -> TranslationValidator:
    text_processor = RenpyProcessor()
    specification = IsSymbolOnlySpec(text_processor) | (
        IsDifferentSpec() & HasTargetAlphabetSpec()
        # IsNotEmptySpec() & NoMixedAlphabetsSpec(text_processor)  # commented for being too strict
    )
    validator = TranslationValidator(specification)

    return validator


def create_default_progress_counter() -> RegexProgressCounter:
    return RegexProgressCounter(
        validator=create_default_validator(),
        dialogues_config=RE_TRANSLATE_CONFIG,
        strings_config=RE_STRINGS_CONFIG,
    )
