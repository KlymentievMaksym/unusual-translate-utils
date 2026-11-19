from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeVar

from translate_utils.core.entities import LineRange
from translate_utils.core.replacer_methods import AVAILABLE_METHODS, CleanMethod

TArgs = TypeVar("TArgs", bound="Args")


def parse_line_ranges_spec(spec: str) -> list[LineRange]:
    """Parse comma-separated 1-based line ranges such as '42', '10-50', '10-', or '-50'."""
    parts = spec.split(",")
    if not parts or any(not part.strip() for part in parts):
        raise ValueError(f"Empty line range entry in '{spec}'.")

    ranges: list[LineRange] = []
    for raw_part in parts:
        part = raw_part.strip()
        if "-" not in part:
            if not part.isdigit():
                raise ValueError(f"Invalid line number '{part}' in '{spec}'.")
            line_num = int(part)
            if line_num < 1:
                raise ValueError(f"Line number must be >= 1, got {line_num}.")
            ranges.append(LineRange(start=line_num, end=line_num))
            continue

        bounds = part.split("-")
        if len(bounds) != 2:
            raise ValueError(f"Invalid line range '{part}' in '{spec}'.")

        start_str, end_str = bounds[0].strip(), bounds[1].strip()
        if not start_str and not end_str:
            raise ValueError(f"Invalid open range '{part}' in '{spec}'.")

        if start_str:
            if not start_str.isdigit():
                raise ValueError(f"Invalid start line '{start_str}' in '{spec}'.")
            start = int(start_str)
            if start < 1:
                raise ValueError(f"Start line must be >= 1, got {start}.")
        else:
            start = 1

        if end_str:
            if not end_str.isdigit():
                raise ValueError(f"Invalid end line '{end_str}' in '{spec}'.")
            end = int(end_str)
            if end < 1:
                raise ValueError(f"End line must be >= 1, got {end}.")
            if end < start:
                raise ValueError(f"End line {end} cannot be smaller than start line {start}.")
        else:
            end = None

        ranges.append(LineRange(start=start, end=end))

    return ranges


def parse_labels_spec(spec: str) -> list[str]:
    """Parse comma-separated dialogue labels or label_hash identifiers."""
    parts = spec.split(",")
    if not parts or any(not part.strip() for part in parts):
        raise ValueError(f"Empty label entry in '{spec}'.")
    return [part.strip() for part in parts]


def split_path_and_ranges(raw_target: str) -> tuple[str, list[LineRange]]:
    """Split an optional ':lines' suffix from a file or directory path safely on Windows/Unix."""
    if ":" not in raw_target:
        return raw_target, []

    prefix, suffix = raw_target.rsplit(":", 1)
    if len(prefix) == 1 and prefix.isalpha():
        return raw_target, []

    if not suffix:
        raise ValueError(f"Missing line range after ':' in '{raw_target}'.")

    return prefix, parse_line_ranges_spec(suffix)


# --- ARGS ---
@dataclass
class Args:
    @classmethod
    def from_namespace(cls: type[TArgs], namespace: argparse.Namespace) -> TArgs:
        return cls(**vars(namespace))


@dataclass(slots=True)
class CleanupRepeatsArgs(Args):
    filepaths: str | None
    name: str | None
    clean_method: CleanMethod

    def is_suitable_clean_method(self) -> bool:
        return self.clean_method in AVAILABLE_METHODS


@dataclass(slots=True)
class CompareDirsArgs(Args):
    dirs: list[str]
    clean_method: CleanMethod
    minor_threshold: float
    match_threshold: float
    auto: bool

    def is_suitable_clean_method(self) -> bool:
        return self.clean_method in AVAILABLE_METHODS


@dataclass(slots=True)
class CheckTranslationProgressArgs(Args):
    filepaths: str | None
    update_readme: str | None


@dataclass
class CheckLanguageArgs(Args):
    filepaths: list[str]
    language: str
    api_url: str
    api_username: str | None
    api_key: str | None
    disabled_rules: list[str] | None
    dicts: list[str] | None
    items_workers: int
    file_workers: int
    lines: list[LineRange] | None = None
    labels: set[str] | None = None
    disable_check_strings: bool = False
    file_line_ranges: dict[Path, list[LineRange]] = field(default_factory=dict)
    dir_line_ranges: dict[Path, list[LineRange]] = field(default_factory=dict)

    def resolve_line_ranges(self, filepath: Path) -> list[LineRange] | None:
        resolved_file = filepath.resolve()
        if resolved_file in self.file_line_ranges:
            return self.file_line_ranges[resolved_file]

        matching_dirs = [
            (dir_path, ranges)
            for dir_path, ranges in self.dir_line_ranges.items()
            if resolved_file.is_relative_to(dir_path)
        ]
        if matching_dirs:
            _, best_ranges = max(matching_dirs, key=lambda item: len(item[0].parts))
            return best_ranges

        if self.lines:
            return self.lines

        return None


# --- ARGPARSE ---
def cleanup_repeats_parse_args() -> CleanupRepeatsArgs:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "filepaths",
        type=str,
        nargs="+",
        help="Relative or Absolute Path to the .rpy translation file",
    )
    parser.add_argument("--name", type=str, default=None, help="Save with new name")
    parser.add_argument(
        "--clean-method",
        type=str,
        default="only_comment",
        help=f"Clean method, available is {list(AVAILABLE_METHODS.keys())}",
    )
    return CleanupRepeatsArgs.from_namespace(parser.parse_args())


def compare_dirs_parse_args() -> CompareDirsArgs:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "dirs",
        type=str,
        nargs=2,
        help="Directories to compare",
    )
    parser.add_argument(
        "--clean-method",
        type=str,
        default="only_comment",
        help=f"Clean method, available is {list(AVAILABLE_METHODS.keys())}",
    )
    parser.add_argument(
        "--minor-threshold",
        type=float,
        default=95.0,
        help="Threshold for Minor changes",
    )
    parser.add_argument(
        "--match-threshold",
        type=float,
        default=60.0,
        help="Threshold for Major changes",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto merge everything suitable",
    )
    return CompareDirsArgs.from_namespace(parser.parse_args())


def check_translation_progress_parse_args() -> CheckTranslationProgressArgs:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "filepaths",
        type=str,
        nargs="*",
        help="Relative or Absolute Path to the .rpy translation file or directory of them",
    )
    parser.add_argument("--update-readme", type=str, default=None, help="Update README")
    return CheckTranslationProgressArgs.from_namespace(parser.parse_args())


def check_language_parse_args() -> CheckLanguageArgs:
    parser = argparse.ArgumentParser(
        description="Check translation grammar and style using LanguageTool API."
    )
    parser.add_argument(
        "filepaths",
        nargs="*",
        help="Files or directories to check, optionally suffixed with :lines such as script.rpy:10-50.",
    )
    parser.add_argument(
        "--lines",
        action="extend",
        nargs="+",
        default=None,
        help="1-based line numbers or ranges to check such as 42, 10-50, 10-, -50, or 10-20,50-60.",
    )
    parser.add_argument(
        "--labels",
        action="extend",
        nargs="+",
        default=None,
        help="Dialogue labels or label_hash keys to check, space- or comma-separated.",
    )
    parser.add_argument(
        "--disable-check-strings",
        action="store_true",
        help="Skip checking UI strings unless line ranges are specified for the file.",
    )
    parser.add_argument(
        "--language",
        "-l",
        default="auto",
        help="Target language code, such as en-US or uk-UA. Defaults to auto.",
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8010/v2",
        help="LanguageTool API URL",
    )
    parser.add_argument(
        "--api-username",
        default=None,
        help="LanguageTool API user username",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="LanguageTool API key",
    )
    parser.add_argument(
        "--disabled-rules",
        nargs="*",
        default=[],
        help="List of LanguageTool rule IDs to ignore.",
    )
    parser.add_argument(
        "--dicts",
        nargs="*",
        default=[],
        help="List of words to ignore.",
    )
    parser.add_argument(
        "--items-workers",
        type=int,
        default=4,
        help="Number of concurrent threads for API requests.",
    )
    parser.add_argument(
        "--file-workers",
        type=int,
        default=4,
        help="Number of concurrent threads for files readers.",
    )

    namespace = parser.parse_args()

    global_lines: list[LineRange] | None = None
    if namespace.lines is not None:
        global_lines = []
        for token in namespace.lines:
            try:
                global_lines.extend(parse_line_ranges_spec(token))
            except ValueError as exc:
                parser.error(str(exc))

    parsed_labels: frozenset[str] | None = None
    if namespace.labels is not None:
        label_tokens: list[str] = []
        for token in namespace.labels:
            try:
                label_tokens.extend(parse_labels_spec(token))
            except ValueError as exc:
                parser.error(str(exc))
        parsed_labels = frozenset(label_tokens)

    cleaned_filepaths: list[str] = []
    file_ranges_acc: defaultdict[Path, list[LineRange]] = defaultdict(list)
    dir_ranges_acc: defaultdict[Path, list[LineRange]] = defaultdict(list)

    for raw_target in namespace.filepaths:
        try:
            clean_path_str, target_ranges = split_path_and_ranges(raw_target)
        except ValueError as exc:
            parser.error(str(exc))

        cleaned_filepaths.append(clean_path_str)
        if target_ranges:
            target_path = Path(clean_path_str)
            resolved = target_path.resolve()
            if target_path.is_dir():
                dir_ranges_acc[resolved].extend(target_ranges)
            elif target_path.is_file():
                file_ranges_acc[resolved].extend(target_ranges)

    return CheckLanguageArgs(
        filepaths=cleaned_filepaths,
        language=namespace.language,
        api_url=namespace.api_url,
        api_username=namespace.api_username,
        api_key=namespace.api_key,
        disabled_rules=namespace.disabled_rules,
        dicts=namespace.dicts,
        items_workers=namespace.items_workers,
        file_workers=namespace.file_workers,
        lines=global_lines,
        labels=parsed_labels,
        disable_check_strings=namespace.disable_check_strings,
        file_line_ranges=dict(file_ranges_acc),
        dir_line_ranges=dict(dir_ranges_acc),
    )
