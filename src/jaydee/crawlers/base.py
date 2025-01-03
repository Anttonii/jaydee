class BaseCrawler:
    """The base instance of all crawlers."""

    def __init__(self):
        self._running = False

    @property
    def running(self):
        return self._running

    @running.setter
    def running(self, val):
        self._running = val
