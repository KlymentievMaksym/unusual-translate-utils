from typing import Protocol

class CleanStrategy(Protocol):
    def __call__(self, text: str, indent: str, comment: str) -> str:
        ...

def add_comment(text: str, indent: str, comment: str) -> str:
    return f"{indent}# {comment}\n{text}"

def only_comment(text: str, indent: str, comment: str) -> str:
    return f"{indent}# {comment}\n"

def empty(text: str, indent: str, comment: str) -> str:
    return ""

AVAILABLE_METHODS = {"add_comment": add_comment, "only_comment": only_comment, "empty": empty}
