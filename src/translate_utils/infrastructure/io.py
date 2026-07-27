import json
from pathlib import Path
from typing import Any

from translate_utils.core.exceptions import FileNotExistsError, FileWriteError

ENCODING_RENPY = "utf-8-sig"
ENCODING_JSON = "utf-8"


def _read_file(filepath: str | Path, encoding: str | None = None) -> str:
    """Base method to read text from a file."""
    try:
        return Path(filepath).read_text(encoding=encoding)
    except FileNotFoundError as e:
        raise FileNotExistsError(f"Filepath {filepath} does not exist") from e


def _write_file(filepath: str | Path, content: str, encoding: str | None = None) -> int:
    """
    Base method to write text to a file.
    Returns the number of characters written.
    """
    try:
        return Path(filepath).write_text(content, encoding=encoding)
    except OSError as e:
        raise FileWriteError(f"Failed to write to {filepath}: {e}") from e


def read_renpy_file(filepath: str | Path) -> str:
    """Read content of a renpy file"""
    return _read_file(filepath, encoding=ENCODING_RENPY)


def write_renpy_file(filepath: str | Path, content: str) -> None:
    """Rewrite content of a renpy file"""
    _write_file(filepath, content, encoding=ENCODING_RENPY)


def read_json_file(filepath: str | Path) -> dict[str, Any]:
    """Read content of a json file and parse it into a dictionary"""
    raw_text = _read_file(filepath, encoding=ENCODING_JSON)
    parsed_data: dict[str, Any] = json.loads(raw_text)
    return parsed_data


def write_json_file(filepath: str | Path, content: Any) -> None:
    """Serialize a Python object into JSON and write it to a file"""
    json_string = json.dumps(content, indent=4, ensure_ascii=False)
    _write_file(filepath, json_string, encoding=ENCODING_JSON)
