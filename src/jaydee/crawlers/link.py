from .base import BaseCrawler
from jaydee.scraper import Scraper, ScraperRule
from jaydee.webscraper import WebScraper
from jaydee.options import CrawlerOptions, WebScraperOptions
from jaydee import utils

import logging
from datetime import datetime

from playwright.async_api import async_playwright

# Setup the link crawler specific logger
logger = logging.getLogger("jd-link-crawler")


class LinkCrawler(BaseCrawler):
    """
    LinkCrawler collects links of interest, adds them into a queue and then scrapes links.

    Args:
        initial_url: the url starting point of the crawling
        callback: a callback function that determines what the crawler should do once it's done with it's URL queue.
        rule: an optional scraper rule to use as the basis for scraping links.
        child_of: an optional child of attribute for where to look for the links that are to be crawled.
        options: optionally provide your own options for the crawler

    Note: The callback is called when the URL queue is empty. For the crawler process to continue, add URLs to the queue
    within the callback or when handling yielded results.
    """

    def __init__(
        self,
        initial_url: str,
        callback=None,
        rule: ScraperRule = None,
        child_of=None,
        options: CrawlerOptions = CrawlerOptions(),
    ):
        super().__init__()

        if not utils.validate_url(initial_url):
            logger.error("Invalid URL passed to Crawler.")

        if rule is None:
            self.rules = self.__get_standard_rules(child_of)
        else:
            self.rules = [rule]

        self.options = options

        self.base_url = utils.parse_base_url(initial_url)
        self.scraper = Scraper(options=self.options._scraper_options).add_rules(
            self.rules
        )

        self._current_page = ""
        self._current_result = {}
        self.on_proceed = callback

        # keep track of seen urls to avoid scraping/crawling them twice
        self.url_queue = []
        self.seen_urls = set()

        self.add_url(initial_url)

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
        Depending on the multithreaded option this will either run multithreaded or with a single thread.

        The crawler runs until it's URL queue is empty and yields links of interest. When the URL queue is empty, Crawler
        invokes it's callback function `on_proceed` which should include any possible additions to the URL queue.

        Yields a list of urls whenever the crawler has successfully scraped a list of links.
        """

        async def fetch(browser, url):
            """Used for fetching HTML documents with session from given URL."""
            logger.info(f"Requesting URL: {url}")

            if not utils.validate_url(url):
                logger.warning(f"Attempted to fetch an invalid URL: {url}, skipping.")
                return None

            page = await browser.new_page()
            # Trick for attempting to bypass restrictions
            await page.add_init_script(
                "delete Object.getPrototypeOf(navigator).webdriver"
            )
            response = await page.goto(url)

            logger.info(f"{url} retrieved with response: {response.status}")

            metadata = {
                "date": datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
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

            await self.options._wait_for_options.async_wait_for(page)
            html = await page.content()

            await page.close()
            return {"doc": html, "metadata": metadata}

        self.running = True

        if self.options._multithreaded:
            webscraper_options = WebScraperOptions(
                wait_for_options=self.options._wait_for_options,
                multithread_options=self.options._multithread_options,
            )
            webscraper = WebScraper(self.scraper, options=webscraper_options)
            await webscraper.start()

            while self.running and self.url_queue:
                webscraper.add_urls(self.url_queue)

                result = await webscraper.scrape_pages()
                logging.info(
                    f"Scraped {webscraper.total} with successes: {webscraper.total_success}, failures: {webscraper.total_failures} and skips: {webscraper.total_skipped}"
                )

                result_links = [
                    self.__add_base_urls(res["links"])
                    for res in result["results"]
                    if "links" in res
                ]

                metadata = {
                    "date": datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
                    "urls": self.url_queue,
                    "success": webscraper.total_success,
                    "failures": webscraper.total_failures,
                    "skipped": webscraper.total_skipped,
                }

                self.current_result = {"links": result_links, "metadata": metadata}
                yield self.current_result

                self.url_queue = []
                if not self.url_queue and self.on_proceed is not None:
                    await self.on_proceed(self)

            await webscraper.quit()
        else:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(
                    headless=self.options._headless, args=utils.get_chrome_arguments()
                )

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
                    if "links" not in result:
                        logger.info(f"No links were found for url: {url}")
                        yield {"links": [], "metadata": fetch_res["metadata"]}
                        continue

                    # Incases where href doesn't have the base url, add it to the URL.
                    full_urls = self.__add_base_urls(result["links"])
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
                logger.info("Crawling ended, cleaning up.")
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

    def __add_base_urls(self, urls: list[str]):
        """Adds base URL to a list of paths without it."""
        return list(
            map(
                lambda x: self.base_url + x if not utils.validate_url(x) else x,
                urls,
            )
        )

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
