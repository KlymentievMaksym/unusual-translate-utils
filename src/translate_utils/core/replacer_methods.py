from enum import Enum
from typing import Final, Protocol


class CleanStrategy(Protocol):
    def __call__(self, text: str, indent: str, comment: str, /) -> str:
        ...

def add_comment(text: str, indent: str, comment: str) -> str:
    return f"{indent}# {comment}\n{text}"

def only_comment(_text: str, indent: str, comment: str) -> str:
    return f"{indent}# {comment}\n"

def empty(_text: str, _indent: str, _comment: str) -> str:
    return ""

class CleanMethod(str, Enum):
    ADD_COMMENT = "add_comment"
    ONLY_COMMENT = "only_comment"
    EMPTY = "empty"


AVAILABLE_METHODS: Final[dict[CleanMethod, CleanStrategy]] = {
    CleanMethod.ADD_COMMENT: add_comment,
    CleanMethod.ONLY_COMMENT: only_comment,
    CleanMethod.EMPTY: empty,
}
