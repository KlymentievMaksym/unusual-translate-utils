import json
from pathlib import Path

from translate_utils.infrastructure.path import DEFAULT_SETTINGS_FILE, reset_file

def save_lines_to_file(original_filepath: str | Path, text_to_replace_with: str, new_name: str | Path | None = None) -> Path:
    original_path = Path(original_filepath)

    if new_name is None:
        out_filepath = original_path
    else:
        new_name = Path(new_name)
        out_filepath = original_path.with_name(f"{new_name}{original_path.suffix}")

    with open(out_filepath, 'w', encoding='utf-8') as f:
        f.write(text_to_replace_with)

    return out_filepath

def save_active_tab(tab_id) -> None:
    settings = load_settings()
    settings["active_tab"] = tab_id
    formated_settings_str = json.dumps(settings)
    reset_file(DEFAULT_SETTINGS_FILE, formated_settings_str)


def load_settings() -> dict:
    with open(DEFAULT_SETTINGS_FILE, "r") as fr:
        return json.load(fr)

def load_active_tab() -> str:
    settings = load_settings()
    return settings.get("active_tab", "Get Tab Error")
