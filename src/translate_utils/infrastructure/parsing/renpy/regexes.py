import re
from dataclasses import dataclass

_SCRIPT_POSITION = r"(?P<script_position>[^/\\]+\.rpy:\d+)"


def _quoted(name: str, n: int) -> str:
    quote_group = r'"""|"'
    return rf"(?P<quote{n}>{quote_group})(?P<{name}>.*?)(?<!\\)(?P=quote{n})"


RE_SIMPLE_TAGS = re.compile(r"\{.*?\}")
RE_TAGS = re.compile(r"\{.*?\}|\[.*?\]")
RE_WORDS = re.compile(r"\w+")

NAME_FORM_MAP = {
    "default": "КУРВААА ПРОПУСТИИИВ ВІДМІІІНЮВАННЯ",
    "nom": "Гравець",
    "gen": "Гравця",
    "dat": "Гравцеві",
    "acc": "Гравця",
    "ins": "Гравцем",
    "loc": "Гравці",
    "voc": "Гравцю",
}
RE_NAME_FORM = re.compile(r"\[name_form\('(\w+)'\)\]")


def name_form_replacer(match: re.Match[str]) -> str:
    grammatical_case = match.group(1)
    word = NAME_FORM_MAP.get(grammatical_case, NAME_FORM_MAP["default"])
    return word


@dataclass(frozen=True, slots=True)
class RegexBlockConfig:
    pattern: re.Pattern[str]
    original_group: str
    translated_group: str


DLG_LABEL = "script_label"
DLG_HASH = "script_hash"
DLG_ORIGINAL_CHAR = "original_character"
DLG_ORIGINAL = "original_text"
DLG_TRANSLATED_CHAR = "translation_character"
DLG_TRANSLATED = "translation_text"

STR_INDENT = "indent"
STR_ORIGINAL = "old_text"
STR_TRANSLATED = "new_text"

# Guaranteed groups: script_position, script_label, script_hash,
# original_character?, original_text, translation_character?, translation_text
RE_TRANSLATE_CONFIG = RegexBlockConfig(
    pattern=re.compile(
        rf"""
        ^ \s* \# \s* (?:.*? [/\\])? {_SCRIPT_POSITION} \s* \n
        ^ translate \s+ \w+ \s+ (?P<{DLG_LABEL}>\w+) _ (?P<{DLG_HASH}>\w+): .* \n

        ^ \s* \# \s* (?:(?P<{DLG_ORIGINAL_CHAR}>\w+) \s+)?
            "(?P<{DLG_ORIGINAL}>(?:[^"\\]|\\.)*)" .* \n

        ^ \s*        (?:(?P<{DLG_TRANSLATED_CHAR}>\w+) \s+)?
            "(?P<{DLG_TRANSLATED}>(?:[^"\\]|\\.)*)" .* $
        """,
        re.MULTILINE | re.VERBOSE,
    ),
    original_group=DLG_ORIGINAL,
    translated_group=DLG_TRANSLATED,
)

# Guaranteed groups: old_text, new_text
# Maybe later will add (?: ^ \s* # \s* (?:[^\n]*? [/\\])? {_SCRIPT_POSITION} \n)
RE_STRINGS_CONFIG = RegexBlockConfig(
    pattern=re.compile(
        rf"""
        ^ (?P<{STR_INDENT}>[ \t]+) old \s+ {_quoted(STR_ORIGINAL, 1)} [ \t]* (?:\#[^\n]*)? \r?\n
        ^ (?P={STR_INDENT}) new \s+ {_quoted(STR_TRANSLATED, 2)} [ \t]* (?:\#[^\n]*)? $
        """,
        re.MULTILINE | re.DOTALL | re.VERBOSE,
    ),
    original_group=STR_ORIGINAL,
    translated_group=STR_TRANSLATED,
)
