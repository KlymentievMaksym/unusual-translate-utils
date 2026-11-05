import concurrent.futures
from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import TypeVar

T_out = TypeVar("T_out")


ExecutorFactory = Callable[[], AbstractContextManager[concurrent.futures.Executor]]
