ISSUE_TYPE_MAP: dict[str, str] = {
    "grammar": "-",
    "misspelling": "~",
    "style": "^",
    "typographical": "+",
    "whitespace": "+",
}

CATEGORY_ID_MAP: dict[str, str] = {
    "GRAMMAR": "-",
    "TYPOS": "~",
    "STYLE": "^",
    "TYPOGRAPHY": "+",
    "PUNCTUATION": "+",
}

PRIORITY: dict[str, int] = {
    "~": 5,  # misspelling
    "-": 4,  # grammar
    "^": 3,  # style
    "+": 2,  # typography / whitespace
    "*": 1,  # fallback
}


def get_underline_char(issue_type: str, category_id: str) -> str:
    normalized_issue = issue_type.lower()
    if normalized_issue in ISSUE_TYPE_MAP:
        return ISSUE_TYPE_MAP[normalized_issue]

    normalized_category = category_id.upper()
    if normalized_category in CATEGORY_ID_MAP:
        return CATEGORY_ID_MAP[normalized_category]

    return "*"
