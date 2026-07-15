from dataclasses import dataclass

from translate_utils.core.rules import check_is_translated

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

    def is_translated(self):
        return check_is_translated(self.original, self.translated)
