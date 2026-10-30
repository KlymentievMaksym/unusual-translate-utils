from pathlib import Path

from translate_utils.infrastructure.io import write_json_file, write_renpy_file


def find_project_root(current_path: Path, marker: str = "src") -> Path:
    for parent in current_path.parents:
        if (parent / marker).exists():
            return parent
    raise FileNotFoundError(marker)


PROJECT_ROOT = find_project_root(Path(__file__), marker="src")
DEFAULT_DIR_FOR_TRANSLATION = PROJECT_ROOT / "game" / "tl" / "ukrainian"

DEFAULT_DIR_FOR_LOGS = PROJECT_ROOT / "translate_logs"
DEFAULT_DIR_FOR_COMPARE_LOGS = DEFAULT_DIR_FOR_LOGS / "compare_logs"
DEFAULT_DIR_FOR_CHECK_LOGS = DEFAULT_DIR_FOR_LOGS / "check_logs"

DEFAULT_DIR_FOR_SETTINGS = PROJECT_ROOT / "translate_settings"

DEFAULT_SETTINGS_FILE = DEFAULT_DIR_FOR_SETTINGS / "settings.json"
DEFAULT_SETTINGS = {"active_tab": "tab_status"}

DEFAULT_LANGUAGE_EXCEPTIONS_FILE = DEFAULT_DIR_FOR_SETTINGS / "lang_exceptions.txt"
DEFAULT_LANGUAGE_EXCEPTIONS = "\n"


def create_default_dirs():
    DEFAULT_DIR_FOR_LOGS.mkdir(exist_ok=True)
    DEFAULT_DIR_FOR_COMPARE_LOGS.mkdir(exist_ok=True)
    DEFAULT_DIR_FOR_CHECK_LOGS.mkdir(exist_ok=True)
    DEFAULT_DIR_FOR_SETTINGS.mkdir(exist_ok=True)
    if not DEFAULT_SETTINGS_FILE.exists():
        write_json_file(DEFAULT_SETTINGS_FILE, DEFAULT_SETTINGS)
    if not DEFAULT_LANGUAGE_EXCEPTIONS_FILE.exists():
        write_renpy_file(DEFAULT_LANGUAGE_EXCEPTIONS_FILE, DEFAULT_LANGUAGE_EXCEPTIONS)
