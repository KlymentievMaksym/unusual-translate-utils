import concurrent.futures
from typing import Callable, ContextManager, TypeVar

T_out = TypeVar("T_out")


ExecutorFactory = Callable[[], ContextManager[concurrent.futures.Executor]]
