import difflib
from dataclasses import dataclass, field
from enum import Enum

from rapidfuzz import fuzz

from translate_utils.core.entities import DialogueLine


class ChangeSeverity(Enum):
    UNCHANGED = "unchanged"
    MINOR = "minor"
    MAJOR = "major"
    ADDED = "added"
    REMOVED = "removed"


@dataclass(frozen=True, slots=True)
class ChangeEntry:
    key: str
    severity: ChangeSeverity
    similarity: float  # 0-100, rapidfuzz scale
    old_text: str | None
    new_text: str | None
    old_translation: str | None = None


@dataclass(slots=True)
class DiffResult:
    entries: list[ChangeEntry] = field(default_factory=list)

    @property
    def unchanged(self) -> list[ChangeEntry]:
        return [e for e in self.entries if e.severity is ChangeSeverity.UNCHANGED]

    @property
    def major(self) -> list[ChangeEntry]:
        return [e for e in self.entries if e.severity is ChangeSeverity.MAJOR]

    @property
    def minor(self) -> list[ChangeEntry]:
        return [e for e in self.entries if e.severity is ChangeSeverity.MINOR]

    @property
    def added(self) -> list[ChangeEntry]:
        return [e for e in self.entries if e.severity is ChangeSeverity.ADDED]

    @property
    def removed(self) -> list[ChangeEntry]:
        return [e for e in self.entries if e.severity is ChangeSeverity.REMOVED]


class StringDiff:
    """
    Compares two dicts of {key: text} and classifies each key's change
    by similarity ratio. Use on dialogues (extract original_text/
    translation_text first) and on ui_strings directly.
    """

    def __init__(self, major_threshold: float = 60.0, minor_threshold: float = 95.0) -> None:
        # similarity < major_threshold  -> MAJOR
        # major_threshold <= sim < minor_threshold -> MINOR
        # sim >= minor_threshold -> UNCHANGED
        self._major_threshold = major_threshold
        self._minor_threshold = minor_threshold

    def compare(self, old: dict[str, str], new: dict[str, str]) -> DiffResult:
        result = DiffResult()
        old_keys, new_keys = set(old), set(new)

        for key in old_keys - new_keys:
            result.entries.append(
                ChangeEntry(key, ChangeSeverity.REMOVED, 0.0, old[key], None)
            )

        for key in new_keys - old_keys:
            result.entries.append(
                ChangeEntry(key, ChangeSeverity.ADDED, 0.0, None, new[key])
            )

        for key in old_keys & new_keys:
            old_text, new_text = old[key], new[key]
            if old_text == new_text:
                result.entries.append(
                    ChangeEntry(key, ChangeSeverity.UNCHANGED, 100.0, old_text, new_text)
                )
                continue

            similarity = fuzz.ratio(old_text, new_text)
            severity = (
                ChangeSeverity.MAJOR if similarity < self._major_threshold
                else ChangeSeverity.MINOR if similarity < self._minor_threshold
                else ChangeSeverity.UNCHANGED
            )
            result.entries.append(
                ChangeEntry(key, severity, similarity, old_text, new_text)
            )

        return result

class DialogueSequenceDiff:
    """
    Compares two lists of DialogueLine preserving file order.
    Uses SequenceMatcher to find identical blocks and rapidfuzz for changed chunks.
    """

    def __init__(self, major_threshold: float = 60.0, minor_threshold: float = 95.0) -> None:
        self._major_threshold = major_threshold
        self._minor_threshold = minor_threshold

    def compare(self, old_lines: list[DialogueLine], new_lines: list[DialogueLine]) -> DiffResult:
        result = DiffResult()

        matcher = difflib.SequenceMatcher(
            None,
            [line.original_text for line in old_lines],
            [line.original_text for line in new_lines]
        )

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            old_chunk = old_lines[i1:i2]
            new_chunk = new_lines[j1:j2]

            if tag == 'equal':
                for old_line, new_line in zip(old_chunk, new_chunk, strict=True):
                    key = f"{new_line.script_label}_{new_line.script_hash}"
                    result.entries.append(
                        ChangeEntry(
                            key=key,
                            severity=ChangeSeverity.UNCHANGED,
                            similarity=100.0,
                            old_text=old_line.original_text,
                            new_text=new_line.original_text,
                            old_translation=old_line.translation_text
                        )
                    )
            elif tag == 'delete':
                for line in old_chunk:
                    key = f"{line.script_label}_{line.script_hash}"
                    result.entries.append(
                        ChangeEntry(
                            key=key,
                            severity=ChangeSeverity.REMOVED,
                            similarity=0.0,
                            old_text=old_line.original_text,
                            new_text=None,
                            old_translation=old_line.translation_text
                        )
                    )
            elif tag == 'insert':
                for line in new_chunk:
                    key = f"{line.script_label}_{line.script_hash}"
                    result.entries.append(
                        ChangeEntry(
                            key=key,
                            severity=ChangeSeverity.ADDED,
                            similarity=0.0,
                            old_text=None,
                            new_text=line.original_text,
                            old_translation=None
                        )
                    )
            elif tag == 'replace':
                min_len = min(len(old_chunk), len(new_chunk))
                for i in range(min_len):
                    old_line = old_chunk[i]
                    new_line = new_chunk[i]
                    similarity = fuzz.ratio(old_line.original_text, new_line.original_text)

                    severity = (
                        ChangeSeverity.MAJOR if similarity < self._major_threshold
                        else ChangeSeverity.MINOR if similarity < self._minor_threshold
                        else ChangeSeverity.UNCHANGED
                    )
                    key = f"{new_line.script_label}_{new_line.script_hash}"
                    result.entries.append(
                        ChangeEntry(
                            key=key,
                            severity=severity,
                            similarity=similarity,
                            old_text=old_line.original_text,
                            new_text=new_line.original_text,
                            old_translation=old_line.translation_text
                        )
                    )

                if len(old_chunk) > min_len:
                    for line in old_chunk[min_len:]:
                        key = f"{line.script_label}_{line.script_hash}"
                        result.entries.append(
                            ChangeEntry(
                                key=key,
                                severity=ChangeSeverity.REMOVED,
                                similarity=0.0,
                                old_text=line.original_text,
                                new_text=None,
                                old_translation=line.translation_text
                            )
                        )
                elif len(new_chunk) > min_len:
                    for line in new_chunk[min_len:]:
                        key = f"{line.script_label}_{line.script_hash}"
                        result.entries.append(
                            ChangeEntry(
                                key=key,
                                severity=ChangeSeverity.ADDED,
                                similarity=0.0,
                                old_text=None,
                                new_text=line.original_text,
                                old_translation=None
                            )
                        )

        return result
