from pathlib import Path

from translate_utils.infrastructure.io import write_json_file


def find_project_root(current_path: Path, marker: str = "game") -> Path:
    for parent in current_path.parents:
        if (parent / marker).exists():
            return parent
    return current_path.parents[3]


def gather_extension_files(paths: list[Path], extension: str = "rpy") -> list[Path]:
    """
    Scans provided paths and returns a sorted list of **.extension** files.
    """
    rpy_files = []
    for target_path in paths:
        if target_path.is_file() and target_path.suffix == f".{extension}":
            rpy_files.append(target_path)
        elif target_path.is_dir():
            rpy_files.extend(target_path.rglob(f"*.{extension}"))
    return sorted(rpy_files, key=lambda path: path.name)


PROJECT_ROOT = find_project_root(Path(__file__), marker="game")
DEFAULT_DIR_FOR_TRANSLATION = PROJECT_ROOT / "game" / "tl" / "ukrainian"

DEFAULT_DIR_FOR_LOGS = PROJECT_ROOT / "translate_logs"
DEFAULT_DIR_FOR_LOGS.mkdir(exist_ok=True)

DEFAULT_DIR_FOR_SETTINGS = PROJECT_ROOT / "translate_settings"
DEFAULT_DIR_FOR_SETTINGS.mkdir(exist_ok=True)

DEFAULT_SETTINGS_FILE = DEFAULT_DIR_FOR_SETTINGS / "settings.json"
DEFAULT_SETTINGS = {"active_tab": "tab_status"}
if not DEFAULT_SETTINGS_FILE.exists():
    write_json_file(DEFAULT_SETTINGS_FILE, DEFAULT_SETTINGS)
