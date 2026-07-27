from translate_utils.infrastructure.io import read_json_file, write_json_file
from translate_utils.infrastructure.path import DEFAULT_SETTINGS_FILE


def save_active_tab(tab_id: str) -> None:
    settings = read_json_file(DEFAULT_SETTINGS_FILE)
    settings["active_tab"] = tab_id
    write_json_file(DEFAULT_SETTINGS_FILE, settings)


def load_active_tab() -> str:
    settings = read_json_file(DEFAULT_SETTINGS_FILE)
    active_tab: str = settings.get("active_tab", "Get Tab Error")
    return active_tab
