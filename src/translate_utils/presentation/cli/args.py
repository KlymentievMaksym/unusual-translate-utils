from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Self

from translate_utils.core.replacer_methods import AVAILABLE_METHODS, CleanMethod


# --- ARGS ---
@dataclass
class Args:
    @classmethod
    def from_namespace(cls, namespace: argparse.Namespace) -> Self:
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
    auto: bool

    def is_suitable_clean_method(self) -> bool:
        return self.clean_method in AVAILABLE_METHODS


@dataclass(slots=True)
class CheckTranslationProgressArgs(Args):
    filepaths: str | None
    update_readme: str | None


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
