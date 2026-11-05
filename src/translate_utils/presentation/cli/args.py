from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import TypeVar

from translate_utils.core.replacer_methods import AVAILABLE_METHODS, CleanMethod

TArgs = TypeVar("TArgs", bound="Args")


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
    max_workers: int


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
        "--clean_method",
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
        "--clean_method",
        type=str,
        default="only_comment",
        help=f"Clean method, available is {list(AVAILABLE_METHODS.keys())}",
    )
    parser.add_argument(
        "--minor_threshold",
        type=float,
        default=95.0,
        help="Threshold for Minor changes",
    )
    parser.add_argument(
        "--match_threshold",
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
        help="Files or directories to check.",
    )
    parser.add_argument(
        "--language",
        "-l",
        default="auto",
        help="Target language code, such as en-US or uk-UA. Defaults to auto.",
    )
    parser.add_argument(
        "--api_url",
        default="https://api.languagetool.org/v2",
        help="LanguageTool API URL",
    )
    parser.add_argument(
        "--api_username",
        default=None,
        help="LanguageTool API user username",
    )
    parser.add_argument(
        "--api_key",
        default=None,
        help="LanguageTool API key",
    )
    parser.add_argument(
        "--disabled_rules",
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
        "--max_workers",
        type=int,
        default=4,
        help="Number of concurrent threads for API requests.",
    )

    return CheckLanguageArgs.from_namespace(parser.parse_args())
