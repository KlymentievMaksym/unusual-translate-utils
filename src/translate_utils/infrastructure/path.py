from pathlib import Path

def find_project_root(current_path: Path, marker: str = "game") -> Path:
    for parent in current_path.parents:
        if (parent / "game").exists():
            return parent
    return current_path.parents[3]

PROJECT_ROOT = find_project_root(Path(__file__))
DEFAULT_DIR_FOR_TRANSLATION = PROJECT_ROOT / "game" / "tl" / "ukrainian"

DEFAULT_DIR_FOR_LOGS = PROJECT_ROOT / "translate_logs"
DEFAULT_DIR_FOR_LOGS.mkdir(exist_ok=True)
