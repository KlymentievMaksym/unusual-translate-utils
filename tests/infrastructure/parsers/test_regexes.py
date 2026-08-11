# test_parsers_regex.py
import re

import pytest

from translate_utils.infrastructure.parsers.regexes import (
    RE_STRINGS_CONFIG,
    RE_TRANSLATE_CONFIG,
    STR_ORIGINAL,
    STR_TRANSLATED,
    _quoted,
)

# ==========================================
# Tests for Helper Functions
# ==========================================

@pytest.mark.parametrize(
    "text, expected",
    [
        ('"""Multiple lines\ntext"""', "Multiple lines\ntext"),
        ('"Single line"', "Single line"),
        ('"""Mixed "quotes" inside"""', 'Mixed "quotes" inside'),
    ]
)
def test_quoted_helper(text: str, expected: str) -> None:
    """Test that the _quoted function correctly captures text inside single or triple quotes."""
    pattern_str = _quoted("my_group", 1)
    pattern = re.compile(pattern_str, re.DOTALL)

    match = pattern.search(text)
    assert match is not None
    assert match.group("my_group") == expected

# ==========================================
# Tests for Dialogue Translation Block Regex
# ==========================================

@pytest.mark.parametrize(
    "dialogue_block, expected_groups",
    [
        pytest.param(
            '# game/script.rpy:15\n'
            'translate ukrainian start_1a2b3c4d:\n'
            '    # e "Hello, world!"\n'
            '    e "Привіт, світе!"',
            {
                "script_position": "script.rpy:15",
                "script_label": "start",
                "script_hash": "1a2b3c4d",
                "original_character": "e",
                "original_text": "Hello, world!",
                "translation_character": "e",
                "translation_text": "Привіт, світе!"
            },
            id="Valid dialogue block with character names"
        ),
        pytest.param(
            '# game/scripts/main.rpy:42\n'
            'translate english no_char_ff9900:\n'
            '    # "Just a narration text." (styles) # comment\n'
            '    "Просто текст автора." (styles) # comment\n'
            '    # "Test." (styls) # coment',
            {
                "script_position": "main.rpy:42",
                "script_label": "no_char",
                "script_hash": "ff9900",
                "original_character": None,
                "original_text": "Just a narration text.",
                "translation_character": None,
                "translation_text": "Просто текст автора."
            },
            id="Valid dialogue block without character names, also with styles and comments"
        ),
        pytest.param(
            '# folder/subfolder/file.rpy:999\n'
            'translate esp char_esc_123456:\n'
            '    # mc "I said \\"Hello\\"!"\n'
            '    mc "Я сказав \\"Привіт\\"!"',
            {
                "script_position": "file.rpy:999",
                "script_label": "char_esc",
                "script_hash": "123456",
                "original_character": "mc",
                "original_text": 'I said \\"Hello\\"!',
                "translation_character": "mc",
                "translation_text": 'Я сказав \\"Привіт\\"!'
            },
            id="Valid dialogue block with escaped quotes"
        ),
    ]
)
def test_re_translate_config_matches(dialogue_block: str, expected_groups: dict) -> None:
    """Test that the RE_TRANSLATE_CONFIG successfully parses valid Ren'Py dialogue blocks."""
    match = RE_TRANSLATE_CONFIG.pattern.search(dialogue_block)

    assert match is not None, "Regex failed to match the dialogue block."

    match_dict = match.groupdict()
    for key, expected_value in expected_groups.items():
        assert match_dict.get(key) == expected_value, f"Mismatch in group '{key}'"


def test_re_translate_config_fails_on_invalid_format() -> None:
    """Test that invalid blocks are ignored."""
    invalid_block = (
        '# Missing script position\n'
        'translate ukrainian start_hash:\n'
        '    # e "Hello"\n'
        '    e "Привіт"\n'
    )
    match = RE_TRANSLATE_CONFIG.pattern.search(invalid_block)
    assert match is None

# ==========================================
# Tests for Strings Translation Block Regex
# ==========================================

@pytest.mark.parametrize(
    "strings_block, expected_old, expected_new, expected_indent",
    [
        pytest.param(
            '    old "Start"\n'
            '    new "Початок"',
            "Start",
            "Початок",
            "    ",
            id="Standard double-quote strings"
        ),
        pytest.param(
            '\told """Long\nStart"""\n'
            '\tnew """Довгий\nПочаток"""',
            "Long\nStart",
            "Довгий\nПочаток",
            "\t",
            id="Multiline triple-quote strings with tabs"
        ),
        pytest.param(
            '    old "Settings" # GUI\n'
            '    new "Налаштування" # GUI',
            "Settings",
            "Налаштування",
            "    ",
            id="Strings with inline comments"
        ),
    ]
)
def test_re_strings_config_matches(
    strings_block: str, expected_old: str, expected_new: str, expected_indent: str
) -> None:
    """Test that the RE_STRINGS_CONFIG successfully parses valid Ren'Py string blocks."""
    match = RE_STRINGS_CONFIG.pattern.search(strings_block)

    assert match is not None, "Regex failed to match the strings block."

    match_dict = match.groupdict()
    assert match_dict.get(STR_ORIGINAL) == expected_old
    assert match_dict.get(STR_TRANSLATED) == expected_new
    assert match_dict.get("indent") == expected_indent
