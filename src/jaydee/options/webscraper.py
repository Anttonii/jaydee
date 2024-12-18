from dataclasses import dataclass

from . import WaitForOptions


@dataclass(init=False)
class WebScraperOptions:
    # Timeout limit for each page in seconds.
    _timeout: int

    # The amount of retries before dropping a page.
    _retries: int

    # The amount of contexts that are within the pool at any given time.
    _pool_size: int

    # Max amount of tasks that can be run concurrently.
    _max_concurrent_tasks: int

    # Options related to waiting for certain events before scraping.
    _wait_for_options: WaitForOptions

    def __init__(
        self,
        timeout: int = 5,
        retries: int = 3,
        pool_size: int = 3,
        max_concurrent_tasks: int = 8,
        wait_for_options=WaitForOptions(),
    ):
        self._timeout = timeout
        self._retries = retries
        self._pool_size = pool_size
        self._max_concurrent_tasks = max_concurrent_tasks
        self._wait_for_options = wait_for_options
