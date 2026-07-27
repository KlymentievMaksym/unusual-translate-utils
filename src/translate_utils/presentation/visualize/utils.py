import textwrap


def truncate(text: str | None, max_width: int = 40) -> str:
    """Safely converts text to a single line and truncates it with an ellipsis."""
    if not text:
        return ""
    clean_text = str(text).replace("\n", " ").replace("\r", "")
    return textwrap.shorten(clean_text, width=max_width, placeholder="...")
