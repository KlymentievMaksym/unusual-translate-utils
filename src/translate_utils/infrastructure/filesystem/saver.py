from translate_utils.infrastructure.filesystem.io import read_json_file, write_json_file
from translate_utils.infrastructure.filesystem.path import AppConfig


def save_active_tab(tab_id: str, config: AppConfig) -> None:
    settings = read_json_file(config.paths.settings_file)
    settings["active_tab"] = tab_id
    write_json_file(config.paths.settings_file, settings)
