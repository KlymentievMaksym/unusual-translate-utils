from collections.abc import Callable
from concurrent.futures import Executor

ExecutorFactory = Callable[[], Executor]
