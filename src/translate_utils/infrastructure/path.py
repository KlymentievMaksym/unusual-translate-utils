from pathlib import Path
import json

def create_file_with_text(filepath: Path, text_to_insert: str) -> None:
    with open(filepath, "w") as fw:
        fw.write(text_to_insert)

def reset_file(filepath: Path, text_to_insert: str):
    create_file_with_text(filepath, text_to_insert)

def find_project_root(current_path: Path, marker: str = "game") -> Path:
    for parent in current_path.parents:
        if (parent / "game").exists():
            return parent
    return current_path.parents[3]

PROJECT_ROOT = find_project_root(Path(__file__))
DEFAULT_DIR_FOR_TRANSLATION = PROJECT_ROOT / "game" / "tl" / "ukrainian"

DEFAULT_DIR_FOR_LOGS = PROJECT_ROOT / "translate_logs"
DEFAULT_DIR_FOR_LOGS.mkdir(exist_ok=True)


DEFAULT_DIR_FOR_SETTINGS = PROJECT_ROOT / "translate_settings"
DEFAULT_DIR_FOR_SETTINGS.mkdir(exist_ok=True)

DEFAULT_SETTINGS_FILE = DEFAULT_DIR_FOR_SETTINGS / "settings.json"
DEFAULT_SETTINGS = {"active_tab": "tab_status"}
if not DEFAULT_SETTINGS_FILE.exists():
    create_file_with_text(DEFAULT_SETTINGS_FILE, json.dumps(DEFAULT_SETTINGS))
