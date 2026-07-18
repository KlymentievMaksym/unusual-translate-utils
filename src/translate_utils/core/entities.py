from dataclasses import dataclass

from translate_utils.core.rules import check_is_translated

@dataclass(slots=True)
class Progress:
    translated: int = 0
    total: int = 0

    @property
    def percentage(self) -> float:
        if self.total == 0:
            return 0.0
        return round((self.translated / self.total) * 100, 2)

@dataclass(slots=True, frozen=True)
class DialogueLine:
    script_position: str
    script_label: str
    script_hash: str
    original_character: str | None
    original_text: str
    translation_character: str | None
    translation_text: str

    def is_translated(self) -> bool:
        return check_is_translated(self.original_text, self.translation_text)
