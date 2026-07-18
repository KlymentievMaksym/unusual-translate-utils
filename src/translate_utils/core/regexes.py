import re


_SCRIPT_POSITION = r"(?P<script_position>[^/\\]+\.rpy:\d+)"

def _quoted(name: str, n: int) -> str:
    quote_group = rf'"""|"'
    return rf'(?P<quote{n}>{quote_group})(?P<{name}>.*?)(?<!\\)(?P=quote{n})'


RE_TAGS = re.compile(r"\{.*?\}|\[.*?\]")
RE_WORDS = re.compile(r'\w+')

# Guaranteed groups: script_position, script_label, script_hash, original_character?, original_text, translation_character?, translation_text
RE_TRANSLATE_BLOCK: re.Pattern[str] = re.compile(
    rf"""
    ^ \s* \# \s* (?:.*? [/\\])? {_SCRIPT_POSITION} \n
    ^ translate \s+ \w+ \s+ (?P<script_label>\w+) _ (?P<script_hash>\w+): \n
    ^ \s* \# \s* (?:(?P<original_character>\w+) \s+)? "(?P<original_text>(?:[^"\\]|\\.)*)" $ \n
    ^ \s*        (?:(?P<translation_character>\w+) \s+)? "(?P<translation_text>(?:[^"\\]|\\.)*)" $
    """,
    re.MULTILINE | re.VERBOSE,
)

# Guaranteed groups: old_text, new_text
# Maybe later will add (?: ^ \s* # \s* (?:[^\n]*? [/\\])? {_SCRIPT_POSITION} \n)
RE_STRINGS_BLOCK: re.Pattern[str] = re.compile(
    rf"""
    ^ (?P<indent>[ \t]+) old \s+ {_quoted("old_text", 1)}
    \n
    (?P=indent) new \s+ {_quoted("new_text", 2)}
    """,
    re.MULTILINE | re.DOTALL | re.VERBOSE,
)
