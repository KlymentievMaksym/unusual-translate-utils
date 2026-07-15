def check_is_translated(original: str, translated: str) -> bool:
    return original != translated and not translated.isascii()