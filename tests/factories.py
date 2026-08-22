from __future__ import annotations

from factory.base import Factory
from factory.declarations import SubFactory

from translate_utils.core.entities import FileProgressSummary, Progress


class ProgressFactory(Factory[Progress]):
    """Factory for generating Progress objects with safe defaults."""

    class Meta:
        model = Progress

    translated: int = 0
    total: int = 0


class FileProgressSummaryFactory(Factory[FileProgressSummary]):
    """Factory for FileProgressSummary. Auto-fills all required Progress fields."""

    class Meta:
        model = FileProgressSummary

    total: SubFactory[ProgressFactory, Progress] = SubFactory(ProgressFactory)
    dialogues: SubFactory[ProgressFactory, Progress] = SubFactory(ProgressFactory)
    strings: SubFactory[ProgressFactory, Progress] = SubFactory(ProgressFactory)
