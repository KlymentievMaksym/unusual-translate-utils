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


def create_default_progress_counter() -> RegexProgressCounter:
    """
    Factory function to assemble and configure the default RegexProgressCounter.
    Encapsulates the complex initialization of specifications and regex configs.
    """
    text_processor = RenpyProcessor()

    specification = IsNotEmptySpec() & (
        IsSymbolOnlySpec(text_processor)
        | (
            IsDifferentSpec() & HasTargetAlphabetSpec()
            # & NoMixedAlphabetsSpec(text_processor)
        )
    )

    return RegexProgressCounter(
        validator=TranslationValidator(specification),
        dialogues_config=RE_TRANSLATE_CONFIG,
        strings_config=RE_STRINGS_CONFIG,
    )
