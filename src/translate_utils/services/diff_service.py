import difflib
from dataclasses import dataclass, field
from enum import Enum

from rapidfuzz import fuzz, process

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
    similarity: float
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
    def __init__(self, min_match_threshold: float = 60.0, minor_threshold: float = 95.0) -> None:
        self._min_match_threshold = min_match_threshold
        self._minor_threshold = minor_threshold

    def compare(self, old: dict[str, str], new: dict[str, str]) -> DiffResult:
        result = DiffResult()
        old_keys, new_keys = set(old), set(new)

        exact_keys = old_keys & new_keys
        for key in exact_keys:
            result.entries.append(
                ChangeEntry(
                    key=key,
                    severity=ChangeSeverity.UNCHANGED,
                    similarity=100.0,
                    old_text=key,
                    new_text=key,
                    old_translation=old[key],
                )
            )

        remained_old_keys = old_keys - exact_keys
        remained_new_keys = new_keys - exact_keys
        remained_new_keys_list = list(remained_new_keys)

        for old_key in remained_old_keys:
            best_match = process.extractOne(old_key, remained_new_keys_list, scorer=fuzz.ratio)
            if not best_match:
                result.entries.append(
                    ChangeEntry(
                        key=old_key,
                        severity=ChangeSeverity.REMOVED,
                        similarity=0.0,
                        old_text=old_key,
                        new_text=None,
                        old_translation=old[old_key],
                    )
                )
                continue

            new_key, score, _ = best_match

            if score >= self._minor_threshold:
                severity = ChangeSeverity.MINOR
            elif score >= self._min_match_threshold:
                severity = ChangeSeverity.MAJOR
            else:
                severity = None

            if severity is not None:
                result.entries.append(
                    ChangeEntry(
                        key=new_key,
                        severity=severity,
                        similarity=score,
                        old_text=old_key,
                        new_text=new_key,
                        old_translation=old[old_key],
                    )
                )
                remained_new_keys_list.remove(new_key)
            else:
                result.entries.append(
                    ChangeEntry(
                        key=old_key,
                        severity=ChangeSeverity.REMOVED,
                        similarity=0.0,
                        old_text=old_key,
                        new_text=None,
                        old_translation=old[old_key],
                    )
                )

        for new_key in remained_new_keys_list:
            result.entries.append(
                ChangeEntry(
                    key=new_key,
                    severity=ChangeSeverity.ADDED,
                    similarity=0.0,
                    old_text=None,
                    new_text=new_key,
                    old_translation=None,
                )
            )

        return result


class DialogueSequenceDiff:
    def __init__(self, min_match_threshold: float = 60.0, minor_threshold: float = 95.0) -> None:
        self._min_match_threshold = min_match_threshold
        self._minor_threshold = minor_threshold

    def compare(self, old_lines: list[DialogueLine], new_lines: list[DialogueLine]) -> DiffResult:
        result = DiffResult()

        matcher = difflib.SequenceMatcher(
            None,
            [line.original_text for line in old_lines],
            [line.original_text for line in new_lines],
        )

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            old_chunk = old_lines[i1:i2]
            new_chunk = new_lines[j1:j2]

            if tag == "equal":
                for old_line, new_line in zip(old_chunk, new_chunk, strict=True):
                    key = f"{new_line.script_label}_{new_line.script_hash}"
                    result.entries.append(
                        ChangeEntry(
                            key=key,
                            severity=ChangeSeverity.UNCHANGED,
                            similarity=100.0,
                            old_text=old_line.original_text,
                            new_text=new_line.original_text,
                            old_translation=old_line.translation_text,
                        )
                    )

            elif tag == "delete":
                for line in old_chunk:
                    key = f"{line.script_label}_{line.script_hash}"
                    result.entries.append(
                        ChangeEntry(
                            key=key,
                            severity=ChangeSeverity.REMOVED,
                            similarity=0.0,
                            old_text=line.original_text,
                            new_text=None,
                            old_translation=line.translation_text,
                        )
                    )

            elif tag == "insert":
                for line in new_chunk:
                    key = f"{line.script_label}_{line.script_hash}"
                    result.entries.append(
                        ChangeEntry(
                            key=key,
                            severity=ChangeSeverity.ADDED,
                            similarity=0.0,
                            old_text=None,
                            new_text=line.original_text,
                            old_translation=None,
                        )
                    )

            elif tag == "replace":
                unmatched_new = list(new_chunk)

                for old_line in old_chunk:
                    best_match = process.extractOne(
                        query=old_line.original_text,
                        choices=[line.original_text for line in unmatched_new],
                        scorer=fuzz.ratio,
                    )

                    if not best_match:
                        key = f"{old_line.script_label}_{old_line.script_hash}"
                        result.entries.append(
                            ChangeEntry(
                                key=key,
                                severity=ChangeSeverity.REMOVED,
                                similarity=0.0,
                                old_text=old_line.original_text,
                                new_text=None,
                                old_translation=old_line.translation_text,
                            )
                        )
                        continue

                    _, score, best_idx = best_match
                    matched_new = unmatched_new[best_idx]

                    if score >= self._minor_threshold:
                        severity = ChangeSeverity.MINOR
                    elif score >= self._min_match_threshold:
                        severity = ChangeSeverity.MAJOR
                    else:
                        severity = None

                    if severity is not None:
                        unmatched_new.pop(best_idx)
                        key = f"{matched_new.script_label}_{matched_new.script_hash}"
                        result.entries.append(
                            ChangeEntry(
                                key=key,
                                severity=severity,
                                similarity=score,
                                old_text=old_line.original_text,
                                new_text=matched_new.original_text,
                                old_translation=old_line.translation_text,
                            )
                        )
                    else:
                        key = f"{old_line.script_label}_{old_line.script_hash}"
                        result.entries.append(
                            ChangeEntry(
                                key=key,
                                severity=ChangeSeverity.REMOVED,
                                similarity=0.0,
                                old_text=old_line.original_text,
                                new_text=None,
                                old_translation=old_line.translation_text,
                            )
                        )

                for new_line in unmatched_new:
                    key = f"{new_line.script_label}_{new_line.script_hash}"
                    result.entries.append(
                        ChangeEntry(
                            key=key,
                            severity=ChangeSeverity.ADDED,
                            similarity=0.0,
                            old_text=None,
                            new_text=new_line.original_text,
                            old_translation=None,
                        )
                    )

        return result
