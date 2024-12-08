from jaydee import Scraper, ScraperRule, ScraperOptions

import logging
from dataclasses import dataclass
import random
from urllib.parse import urlparse

from playwright.async_api import async_playwright

# Setup the scraper specific logger
logger = logging.getLogger("jd-crawler")

# Mock user agent values to use randomly.
DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
]


@dataclass(init=False)
class CrawlerOptions:
    """Options for the crawler."""

    # Whether or not the instance of Playwright will be headless.
    _headless: bool

    # If not empty, the crawler wait for selector be present before parsing HTML.
    _waitForSelector: str

    # Whether or not to wait for the network to be idle for half a second before parsing HTML.
    _waitForIdle: bool

    # User agent to use for crawling
    _userAgents: list[str]

    # Options for the base scraper
    _scraperOptions: ScraperOptions

    def __init__(
        self,
        headless=True,
        waitForSelector="",
        waitForIdle=False,
        userAgents=DEFAULT_USER_AGENTS,
        scraperOptions=ScraperOptions(True),
    ):
        """Setup default values."""
        self._headless = headless
        self._waitForSelector = waitForSelector
        self._waitForIdle = waitForIdle
        self._userAgents = userAgents
        self._scraperOptions = scraperOptions


class Crawler:
    """
    Crawler collects links of interest, adds them into a queue and then scrapes links.

    Args:
        initial_url: the url starting point of the crawling
        callback: a callback function that determines what the crawler should do once it's done with it's URL queue.
        rule: an optional scraper rule to use as the basis for scraping links.
        child_of: an optional child of attribute for where to look for the links that are to be crawled.
        options: optionally provide your own options for the crawler

    Note: The callback is called when the URL queue is empty. For the crawler process to continue, add URLs to the queue
    within the callback.
    """

    def __init__(
        self,
        initial_url: str,
        callback,
        rule: ScraperRule = None,
        child_of=None,
        options: CrawlerOptions = CrawlerOptions(),
    ):
        if not self.__validate_url(initial_url):
            logger.error("Invalid URL passed to Crawler.")

        if rule is None:
            self.rules = self.__get_standard_rules(child_of)
        else:
            self.rules = [rule]

        self.options = options

        self.base_url = self.__parse_base_url(initial_url)
        self.scraper = Scraper(options=self.options._scraperOptions).add_rules(
            self.rules
        )

        self._current_page = ""
        self.on_proceed = callback

        # keep track of seen urls to avoid scraping/crawling them twice
        self.url_queue = []
        self.seen_urls = set()

        self.add_url(initial_url)
        self.running = False

    def __get_standard_rules(self, child_of) -> list[ScraperRule]:
        """
        Utility function that sets up default scraping rules.

        By default we scrape every single link, setting custom attributes is possible within the constructor.
        """
        return [
            ScraperRule(
                target="links",
                attributes={"element": "a", "property": "href", "child_of": child_of},
            )
        ]

    def __parse_base_url(self, url: str) -> str:
        """
        Parses base part of the url.

        For example given url https://example.com/foo/bar?id=1 return https://example.com

        Args:
            url: url to parse base url from.
        Returns:
            str: the base url of the given url.
        """
        parsed_url = urlparse(url)
        return parsed_url.scheme + "://" + parsed_url.netloc

    def __validate_url(self, url: str) -> bool:
        """
        Validates URL to see if it's valid.

        Args:
            url: url to validate
        Returns:
            bool: whether or not the url is valid.
        """
        try:
            parsed_url = urlparse(url)
            return all([parsed_url.scheme, parsed_url.netloc])
        except AttributeError:
            return False

    def __get_random_user_agent(self) -> str | None:
        """Returns a random user agent from list of defaults."""
        if len(self.options._userAgents) == 0:
            logger.warning(
                "No user agents set, will default to Playwrights user agent."
            )
            return None

        if len(self.options._userAgents) == 1:
            logger.warning("It's suggested to use more than one user agent.")

        return random.choice(self.options._userAgents)

    async def start(self):
        """
        Starts the crawling coroutine.

        This includes making requests, scraping links and returning them.

        The crawler runs until it's URL queue is empty and yields links of interest. When the URL queue is empty, Crawler
        invokes it's callback function `on_proceed` which should include any possible additions to the URL queue.
        """

        # Start running
        self.running = True

        async def fetch(browser, url):
            """Used for fetching HTML documents with session from given URL."""
            logger.info(f"Requesting URL: {url}")

            if not self.__validate_url(url):
                logger.warning(f"Attempted to fetch an invalid URL: {url}, skipping.")
                return None

            page = await browser.new_page()

            response = await page.goto(url)

            logger.info(f"retrieved with response: {response.status}")

            if response.status != 200:
                logger.warning(
                    f"Failed to fetch {url} with status code: {response.status}, stopping.."
                )
                self.running = False
                return

            # If wait for idle is enabled, wait for network to be idle for half a second.
            if self.options._waitForIdle is not None:
                await page.wait_for_load_state("networkidle")
            # Alternatively a selector can be used.
            elif (
                self.options._waitForSelector is not None
                and self.options._waitForSelector != ""
            ):
                await page.wait_for_selector(self.options._waitForSelector)

            html = await page.content()
            await page.close()

            return html

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self.options._headless)

            while self.url_queue and self.running:
                # Create browser context with a random user agent.
                context = await browser.new_context(
                    user_agent=self.__get_random_user_agent(),
                    viewport={"width": 1920, "height": 1080},
                )

                url = self.url_queue.pop()
                html = await fetch(context, url)

                # If HTML is none, continue.
                # fetch() takes care of logging information.
                if html is None:
                    continue

                self._current_page = html
                self.scraper.document = html

                result = self.scraper.scrape()

                # If there are no links found, stop.
                if len(result["links"]) == 0:
                    logger.info("No links were found, stopping..")
                    self.stop()
                    yield []
                    continue

                # Incases where href doesn't have the base url, add it to the URL.
                full_urls = list(
                    map(
                        lambda x: self.base_url + x
                        if not self.__validate_url(x)
                        else x,
                        result["links"],
                    )
                )

                yield full_urls

                # We have yielded first patch of links
                # proceed according to callback or if no new urls are added
                # to the queue, terminate.
                if not self.url_queue and self.on_proceed is not None:
                    self.on_proceed(self)

            # Clean up
            await browser.close()

    def stop(self):
        """Stops the crawler."""
        self.running = False

    def add_url(self, url: str):
        """Adds a given url to the queue."""
        if url in self.seen_urls:
            logger.info(f"URL {url} already crawled, will be skipped.")
            return

        self.seen_urls.add(url)
        self.url_queue.append(url)

    @property
    def current_page(self):
        return self._current_page
