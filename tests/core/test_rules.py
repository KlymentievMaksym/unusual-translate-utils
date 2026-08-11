import pytest

from translate_utils.core.rules import (
    HasTargetAlphabetSpec,
    IsDifferentSpec,
    IsNotEmptySpec,
    IsSymbolOnlySpec,
    NoMixedAlphabetsSpec,
)
from translate_utils.infrastructure.factories import create_default_validator
from translate_utils.infrastructure.parsers.processors import RenpyProcessor


@pytest.fixture
def text_processor() -> RenpyProcessor:
    """Provides a reusable instance of RenpyProcessor."""
    return RenpyProcessor()


# ==========================================
# Tests for individual Specification Rules
# ==========================================


@pytest.mark.parametrize(
    "original, translated, expected",
    [
        ("_", "Привіт", True),
        ("_", "", False),
        ("_", "   ", False),
    ],
)
def test_is_not_empty_spec(original: str, translated: str, expected: bool) -> None:
    """Test that empty or whitespace-only translations are rejected."""
    spec = IsNotEmptySpec()
    assert spec.is_satisfied_by(original, translated) is expected


@pytest.mark.parametrize(
    "original, translated, expected",
    [
        ("Hello", "Привіт", True),  # Different
        ("Hello", "Hello", False),  # Exact match (not translated)
        ("Hello", "hello", True),  # Case difference (technically different)
    ],
)
def test_is_different_spec(original: str, translated: str, expected: bool) -> None:
    """Test that the translation actually changes the original text."""
    spec = IsDifferentSpec()
    assert spec.is_satisfied_by(original, translated) is expected


@pytest.mark.parametrize(
    "original, translated, expected",
    [
        ("_", "Привіт", True),
        ("_", "Hello, bro", False),
        ("_", "...", False),
        ("_", "Привіт!", True),
    ],
)
def test_has_target_alphabet_spec(original: str, translated: str, expected: bool) -> None:
    """Test that the translation contains non-ASCII characters."""
    spec = HasTargetAlphabetSpec()
    assert spec.is_satisfied_by(original, translated) is expected


@pytest.mark.parametrize(
    "original, translated, expected",
    [
        ("_", "Привіт", True),
        ("_", "Hello", True),
        ("_", "Привіт, John!", True),
        ("_", "Привiт", False),
        ("_", "Hellт", False),
        ("_", "Текст {tag_m1xed}", True),
    ],
)
def test_no_mixed_alphabets_spec(
    text_processor: RenpyProcessor, original: str, translated: str, expected: bool
) -> None:
    """Test that individual words do not mix alphabets, ignoring system tags."""
    spec = NoMixedAlphabetsSpec(text_processor)
    assert spec.is_satisfied_by(original, translated) is expected


@pytest.mark.parametrize(
    "original, translated, expected",
    [
        ("!?}{.", "_", True),  # Only symbols
        ("... ..", "_", True),  # Only punctuation and spaces
        ("...{image=corazon}~", "_", True),  # Symbols + Structural Tag
        ("Hello", "_", False),  # Contains letters
        ("Hello!{image=corazon}~", "_", False),  # Contains letters alongside a tag
    ],
)
def test_is_symbol_only_spec(
    text_processor: RenpyProcessor, original: str, translated: str, expected: bool
) -> None:
    """Test that the original string consists entirely of symbols, ignoring tags."""
    spec = IsSymbolOnlySpec(text_processor)
    assert spec.is_satisfied_by(original, translated) is expected


# ==========================================
# Tests for the Composite / Facade
# ==========================================


@pytest.mark.parametrize(
    "original, translated, expected",
    [
        pytest.param("Hello", "Привіт", True, id="Valid translation"),
        pytest.param("Hello", "Hello", False, id="Fails IsDifferentSpec"),
        pytest.param("Hello", "   ", False, id="Fails IsNotEmptySpec"),
        pytest.param("Hello", "Yes", False, id="Fails HasTargetAlphabetSpec (Only ASCII)"),
        pytest.param("Hello!...", "Привіт!...", True, id="Valid translation with punctuation"),
        # pytest.param("Hello!...", "Hellт!... ..", False, id="Fails NoMixedAlphabetsSpec"),
        pytest.param("!?}{.", "!?}{.", True, id="Symbols only (Valid)"),
        pytest.param("... ..", "... ..", True, id="Symbols only (Valid)"),
        pytest.param("...{image=corazon}~", "...{image=corazon}~", True, id="Symbols + Tag only"),
        pytest.param(
            "Hello!{image=corazon}~",
            "Привіт!{image=corazon}~",
            True,
            id="Text translated, tag kept",
        ),
        pytest.param(
            "Hello!{image=corazon}~",
            "Hello!{image=corazon}~",
            False,
            id="Fails IsDifferentSpec (Untranslated)",
        ),
        pytest.param(
            "~~{image=/bg/icons/heart_text.png}{image=/bg/icons/heart_text.png}",
            "~~{image=/bg/icons/heart_text.png}{image=/bg/icons/heart_text.png}",
            True,
            id="No Text, only symbols, tag kept",
        ),
        pytest.param(
            "old:1783157112.3502007_1",
            "new:1783157112.3502007_1",
            False,
            id="Fails HasTargetAlphabetSpec",
        ),
        # pytest.param(
        #     "Hello!{image=corazon}~",
        #     "Hellт!{image=corazon}~",
        #     False,
        #     id="Fails NoMixedAlphabetsSpec with tags",
        # ),
    ],
)
def test_check_is_translated_facade(original: str, translated: str, expected: bool) -> None:
    """
    Integration test for the facade function.
    Ensures that all combined rules (VALID_TRANSLATION_SPEC) work together correctly.
    """
    validator = create_default_validator()

    result = validator.check_is_translated(original, translated)

    assert result is expected
