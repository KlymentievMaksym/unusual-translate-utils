from translate_utils.core.rules import (
    HasTargetAlphabetSpec,
    # NoMixedAlphabetsSpec
    IsDifferentSpec,
    IsNotEmptySpec,
    IsSymbolOnlySpec,
    TranslationValidator,
)
from translate_utils.infrastructure.counter import RegexProgressCounter
from translate_utils.infrastructure.parsers.processors import RenpyProcessor
from translate_utils.infrastructure.parsers.regexes import RE_STRINGS_CONFIG, RE_TRANSLATE_CONFIG


def create_default_validator() -> TranslationValidator:
    """
    Factory function to assemble and configure the default TranslationValidator.
    """
    text_processor = RenpyProcessor()
    specification = (
        IsSymbolOnlySpec(text_processor)
        | (
            IsDifferentSpec() & HasTargetAlphabetSpec()
            # IsNotEmptySpec() & NoMixedAlphabetsSpec(text_processor)
        )
    )
    validator = TranslationValidator(specification)

    return validator


def create_default_progress_counter() -> RegexProgressCounter:
    """
    Factory function to assemble and configure the default RegexProgressCounter.
    Encapsulates the complex initialization of specifications and regex configs.
    """
    return RegexProgressCounter(
        validator=create_default_validator(),
        dialogues_config=RE_TRANSLATE_CONFIG,
        strings_config=RE_STRINGS_CONFIG,
    )
