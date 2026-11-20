from __future__ import annotations

import re

_CYRILLIC_CHARS = "А-Яа-яЁёІіЇїЄєҐґ"
_WORD_CHARS = f"{_CYRILLIC_CHARS}A-Za-z'’"

_RE_CYRILLIC_CHAR = re.compile(f"[{_CYRILLIC_CHARS}]")
_RE_REPEATED_CYRILLIC = re.compile(rf"([{_CYRILLIC_CHARS}])\1{{2,}}", re.IGNORECASE)
_LEADING_DASH_BOUNDARY = r"(?:^|(?<=[\s(\[\{\"'«„“‘…])|(?<=\.\.\.))"
_RE_LEADING_GLUED_DASH = re.compile(rf"{_LEADING_DASH_BOUNDARY}[-–—]+(?=[{_CYRILLIC_CHARS}A-Za-z])")
RE_LEADING_GLUED_DASH_WORD = re.compile(
    rf"{_LEADING_DASH_BOUNDARY}[-–—]+([{_WORD_CHARS}]+(?:[-–—][{_WORD_CHARS}]+)*)"
)
_RE_HYPHENATED_WORD = re.compile(rf"[{_WORD_CHARS}]+(?:[-–—][{_WORD_CHARS}]+)+")
_RE_SPLIT_DELIMITERS = re.compile(r"([-–—])")
_RE_TRAILING_GLUED_DASH = re.compile(rf"(?<=[{_CYRILLIC_CHARS}A-Za-z])[-–—]+(?![{_WORD_CHARS}0-9])")


def _normalize_apostrophes(text: str) -> str:
    return text.replace("’", "'")


def _collapse_stutter_chain(match: re.Match[str]) -> str:
    token = match.group(0)
    if not _RE_CYRILLIC_CHAR.search(token):
        return token

    parts = _RE_SPLIT_DELIMITERS.split(token)
    segments = parts[0::2]
    delimiters = parts[1::2]

    count = len(segments)
    dropped = [False] * count
    force_upper = [seg[0].isupper() for seg in segments]

    for i in range(count - 1):
        prefix_norm = _normalize_apostrophes(segments[i]).lower()
        prefix_len = len(prefix_norm)

        for j in range(i + 1, count):
            candidate_norm = _normalize_apostrophes(segments[j]).lower()
            candidate_len = len(candidate_norm)
            is_stutter_prefix = candidate_len > prefix_len and candidate_norm.startswith(
                prefix_norm
            )
            is_single_letter_repeat = (
                prefix_len == 1 and candidate_len == 1 and candidate_norm == prefix_norm
            )
            if is_stutter_prefix or is_single_letter_repeat:
                dropped[i] = True
                if force_upper[i]:
                    force_upper[j] = True
                break

    kept_parts: list[str] = []
    for idx, segment in enumerate(segments):
        if dropped[idx]:
            continue
        if force_upper[idx] and segment[0].islower():
            segment = segment[0].upper() + segment[1:]
        kept_parts.append(segment)
        if idx < len(delimiters):
            kept_parts.append(delimiters[idx])

    return "".join(kept_parts)


class StutterNormalizer:
    """Collapses Cyrillic letter stretching, glued stutter prefixes, and glued edge dashes."""

    def normalize(self, text: str) -> str:
        result = _RE_REPEATED_CYRILLIC.sub(lambda m: m.group(1), text)
        result = _RE_LEADING_GLUED_DASH.sub("", result)
        result = _RE_HYPHENATED_WORD.sub(_collapse_stutter_chain, result)
        result = _RE_TRAILING_GLUED_DASH.sub("", result)
        return result
