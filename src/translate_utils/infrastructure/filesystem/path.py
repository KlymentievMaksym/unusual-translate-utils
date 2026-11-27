from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any

from translate_utils.infrastructure.filesystem.io import (
    read_json_file,
    write_json_file,
    write_renpy_file,
)

_DEFAULT_LANGUAGE_EXCEPTIONS = "\n"


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    logs_dir: Path
    common_logs_dir: Path
    compare_logs_dir: Path
    check_logs_dir: Path
    settings_dir: Path
    settings_file: Path
    language_exceptions_file: Path
    default_translation_dir: Path

    @classmethod
    def from_root(cls, root: Path) -> "ProjectPaths":
        logs_dir = root / "translate_logs"
        settings_dir = root / "translate_settings"
        return cls(
            root=root,
            logs_dir=logs_dir,
            common_logs_dir=logs_dir / "common_logs",
            compare_logs_dir=logs_dir / "compare_logs",
            check_logs_dir=logs_dir / "check_logs",
            settings_dir=settings_dir,
            settings_file=settings_dir / "settings.json",
            language_exceptions_file=settings_dir / "lang_exceptions.txt",
            default_translation_dir=root / "game" / "tl" / "ukrainian",
        )


def _resolve_translation_dir(raw_value: Any, paths: ProjectPaths) -> Path:
    if not raw_value:
        return paths.default_translation_dir
    candidate = Path(str(raw_value))
    if candidate.is_absolute():
        return candidate
    return (paths.root / candidate).resolve()


@dataclass(frozen=True)
class Settings:
    dir_for_translation: Path
    active_tab: str = "tab_status"

    @classmethod
    def defaults(cls, paths: ProjectPaths) -> "Settings":
        return cls(dir_for_translation=paths.default_translation_dir)

    @classmethod
    def from_dict(cls, data: dict[str, Any], paths: ProjectPaths) -> "Settings":
        valid_keys = {f.name for f in fields(cls)} - {"dir_for_translation"}
        kwargs: dict[str, Any] = {k: v for k, v in data.items() if k in valid_keys}
        kwargs["dir_for_translation"] = _resolve_translation_dir(
            data.get("dir_for_translation"), paths
        )
        return cls(**kwargs)

    def to_dict(self, paths: ProjectPaths) -> dict[str, Any]:
        raw = asdict(self)
        raw["dir_for_translation"] = (
            None
            if self.dir_for_translation == paths.default_translation_dir
            else str(self.dir_for_translation)
        )
        return raw


@dataclass(frozen=True)
class AppConfig:
    paths: ProjectPaths
    settings: Settings


def initialize_config(project_root: Path | None = None) -> AppConfig:
    root = (project_root or Path.cwd()).resolve()
    paths = ProjectPaths.from_root(root)

    for directory in (
        paths.logs_dir,
        paths.compare_logs_dir,
        paths.check_logs_dir,
        paths.settings_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    if not paths.settings_file.exists():
        settings = Settings.defaults(paths)
        write_json_file(paths.settings_file, settings.to_dict(paths))
    else:
        loaded: dict[str, Any] = read_json_file(paths.settings_file)
        settings = Settings.from_dict(loaded, paths)
        serialized = settings.to_dict(paths)
        if serialized != loaded:
            write_json_file(paths.settings_file, serialized)

    if not paths.language_exceptions_file.exists():
        write_renpy_file(paths.language_exceptions_file, _DEFAULT_LANGUAGE_EXCEPTIONS)

    return AppConfig(
        paths=paths,
        settings=settings,
    )
