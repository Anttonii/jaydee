from dataclasses import dataclass

from . import ScraperOptions, WaitForOptions


@dataclass(init=False)
class CrawlerOptions:
    """Options for the crawler."""

    # Whether or not the instance of Playwright will be headless.
    _headless: bool

    # Options related to waiting for certain events before scraping.
    _wait_for_options: WaitForOptions

    # Options for the base scraper
    _scraper_options: ScraperOptions

    # Whether or not the crawler only stays within it's base URLs domain.
    _strict: bool

    # Whether or not the crawler should be run multithreaded.
    _multithreaded: bool

    def __init__(
        self,
        headless=True,
        wait_for_options=WaitForOptions(),
        scraper_options=ScraperOptions(True),
        strict=True,
        multithreaded=False,
    ):
        """Setup default values."""
        self._headless = headless
        self._wait_for_options = wait_for_options
        self._scraper_options = scraper_options
        self._strict = strict
        self._multithreaded = multithreaded
