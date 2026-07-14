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

    def is_translated(self):
        return self.original != self.translated and not self.translated.isascii()
