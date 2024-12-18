from dataclasses import dataclass


@dataclass(init=False)
class MultithreadOptions:
    # The amount of contexts that are within the pool at any given time.
    _pool_size: int

    # Max amount of tasks that can be run concurrently.
    _max_concurrent_tasks: int

    def __init__(
        self,
        pool_size: int = 2,
        max_concurrent_tasks: int = 4,
    ):
        self._pool_size = pool_size
        self._max_concurrent_tasks = max_concurrent_tasks
