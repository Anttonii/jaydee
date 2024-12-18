from dataclasses import dataclass

from . import WaitForOptions, MultithreadOptions


@dataclass(init=False)
class WebScraperOptions:
    # Timeout limit for each page in seconds.
    _timeout: int

    # The amount of retries before dropping a page.
    _retries: int

    # Options for multithreading
    _multithread_options: MultithreadOptions

    # Options related to waiting for certain events before scraping.
    _wait_for_options: WaitForOptions

    def __init__(
        self,
        timeout: int = 5,
        retries: int = 3,
        wait_for_options=WaitForOptions(),
        multithread_options=MultithreadOptions(),
    ):
        self._timeout = timeout
        self._retries = retries
        self._wait_for_options = wait_for_options
        self._multithread_options = multithread_options
