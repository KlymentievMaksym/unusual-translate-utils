from dataclasses import dataclass
from typing import Generic, TypeVar

T_out = TypeVar("T_out")


@dataclass(slots=True)
class FileCache(Generic[T_out]):
    mtime: float
    content: T_out
