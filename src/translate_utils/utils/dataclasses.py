import argparse

from dataclasses import dataclass

@dataclass(slots=True)
class Progress:
    translated: int = 0
    total: int = 0

@dataclass(slots=True)
class DialogueLine:
    script_pos: str | None
    character: str | None
    original: str
    translated: str


@dataclass
class Args:
    @classmethod
    def from_namespace(cls, namespace: argparse.Namespace):
        return cls(**vars(namespace))

@dataclass(slots=True)
class CleanupRepeatsArgs(Args):
    filepaths: str | None
    name: str | None

@dataclass(slots=True)
class CheckTranslationProgressArgs(Args):
    filepaths: str | None
    update_readme: bool
