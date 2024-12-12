from .scraper import Scraper, ScraperRule, ScraperOptions
from . import utils

import logging
from dataclasses import dataclass
from datetime import datetime

from playwright.async_api import async_playwright

# Setup the scraper specific logger
logger = logging.getLogger("jd-crawler")


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

    # Whether or not the crawler only stays within it's base URLs domain.
    _strict: bool

    def __init__(
        self,
        headless=True,
        waitForSelector=None,
        waitForIdle=False,
        scraperOptions=ScraperOptions(True),
        strict=True,
    ):
        """Setup default values."""
        self._headless = headless
        self._waitForSelector = waitForSelector
        self._waitForIdle = waitForIdle
        self._scraperOptions = scraperOptions
        self._strict = strict


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
        if not utils.validate_url(initial_url):
            logger.error("Invalid URL passed to Crawler.")

        if rule is None:
            self.rules = self.__get_standard_rules(child_of)
        else:
            self.rules = [rule]

        self.options = options

        self.base_url = utils.parse_base_url(initial_url)
        self.scraper = Scraper(options=self.options._scraperOptions).add_rules(
            self.rules
        )

        self._current_page = ""
        self._current_result = {}
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

    async def start(self):
        """
        Starts the crawling coroutine.

        This includes making requests, scraping links and returning them.

        The crawler runs until it's URL queue is empty and yields links of interest. When the URL queue is empty, Crawler
        invokes it's callback function `on_proceed` which should include any possible additions to the URL queue.

        yields a list of urls whenever the crawler has succesfully scraped a list of links.
        """

        # Start running
        self.running = True

        async def fetch(browser, url):
            """Used for fetching HTML documents with session from given URL."""
            logger.info(f"Requesting URL: {url}")

            if not utils.validate_url(url):
                logger.warning(f"Attempted to fetch an invalid URL: {url}, skipping.")
                return None

            page = await browser.new_page()
            response = await page.goto(url)

            logger.info(f"{url} retrieved with response: {response.status}")

            metadata = {
                "time": datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
                "url": url,
                "base_url": utils.parse_base_url(url),
                "domain": utils.parse_domain(url),
                "status": response.status,
            }

            if not response.ok:
                logger.warning(
                    f"Failed to fetch {url} with status code: {response.status}, skipping.."
                )
                await page.close()
                return {"doc": None, "metadata": metadata}

            # If wait for idle is enabled, wait for network to be idle for half a second.
            # Takes precedence over waiting for a selector.
            if self.options._waitForIdle is not None:
                await page.wait_for_load_state("networkidle")
            # Alternatively a selector can be used.
            elif self.options._waitForSelector is not None:
                await page.wait_for_selector(self.options._waitForSelector)

            html = await page.content()
            await page.close()

            return {"doc": html, "metadata": metadata}

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self.options._headless)

            while self.url_queue and self.running:
                self.current_result = {}
                self.current_page = ""

                # Create browser context with a random user agent.
                context = await browser.new_context(
                    user_agent=utils.get_random_user_agent(),
                    viewport={"width": 1920, "height": 1080},
                )

                url = self.url_queue.pop()
                fetch_res = await fetch(context, url)

                if fetch_res is None:
                    continue

                # If HTML document is none, continue.
                # fetch() takes care of logging information.
                if fetch_res["doc"] is None:
                    yield {"metadata": fetch_res["metadata"]}
                    continue

                self.current_page = fetch_res["doc"]
                result = self.scraper.scrape(self.current_page)

                # If there are no links found, skip.
                if len(result["links"]) == 0:
                    logger.info(f"No links were found for url: {url}")
                    yield {"metadata": fetch_res["metadata"]}
                    continue

                # Incases where href doesn't have the base url, add it to the URL.
                full_urls = list(
                    map(
                        lambda x: self.base_url + x if not utils.validate_url(x) else x,
                        result["links"],
                    )
                )

                self.current_result = {
                    "links": full_urls,
                    "metadata": fetch_res["metadata"],
                }

                yield self.current_result

                # We have yielded first patch of links
                # proceed according to callback or if no new urls are added
                # to the queue, terminate.
                if not self.url_queue and self.on_proceed is not None:
                    await self.on_proceed(self)

            # Clean up
            await browser.close()

    def stop(self):
        """Stops the crawler."""
        self.running = False

    def add_url(self, url: str):
        """Adds a given url to the queue."""
        if self.options._strict:
            if utils.parse_base_url(url) != self.base_url:
                logger.info(f"URL {url} outside of the domain of base URL, skipping..")
                return

        if url in self.seen_urls:
            logger.info(f"URL {url} already crawled, will be skipped.")
            return

        self.seen_urls.add(url)
        self.url_queue.append(url)

    def get_links(self) -> list[str]:
        """Returns list of links if we currently have a result otherwise an empty list."""
        if "links" in self.current_result:
            return self.current_result["links"]
        else:
            return []

    @property
    def current_page(self):
        return self._current_page

    @current_page.setter
    def current_page(self, val):
        self._current_page = val

    @property
    def current_result(self):
        return self._current_result

    @current_result.setter
    def current_result(self, val):
        self._current_result = val
