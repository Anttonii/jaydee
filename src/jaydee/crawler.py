from jaydee import Scraper, ScraperRule

import logging
from urllib.parse import urlparse

import aiohttp

# Setup the scraper specific logger
logger = logging.getLogger("jd-crawler")


class Crawler:
    """
    Crawler collects links of interest, adds them into a queue and then scrapes data of interest.

    Args:
        initial_url: the url starting point of the crawling
        callback: a callback function that determines what the crawler should do once it's done with it's URL queue.
        child_of: an optional child of attribute for where to look for the links that are to be crawled.

    The callback is called
    """

    def __init__(
        self, initial_url: str, callback, rule: ScraperRule = None, child_of=None
    ):
        if not self.__validate_url(initial_url):
            logger.error("Invalid URL passed to Crawler.")

        if rule is None:
            self.rules = self.__get_standard_rules(child_of)
        else:
            self.rules = [rule]

        self.base_url = self.__parse_base_url(initial_url)
        self.scraper = Scraper().add_rules(self.rules)

        self._current_page = ""
        self.on_proceed = callback

        # keep track of seen urls to avoid accidentally scraping/crawling them twice
        self.url_queue = []
        self.seen_urls = set()

        self.add_url(initial_url)
        self.running = False

    def __get_standard_rules(self, child_of) -> list[ScraperRule]:
        """
        Utility function that sets up scraping rules.

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

    async def start(self):
        """
        Starts the crawling process.

        This includes making requests, scraping links and then adding links to
        the queue.

        The crawler runs until it's URL queue is empty and yields links of interest.
        """

        # Start running
        self.running = True

        async def fetch(session, url):
            """Used for fetching HTML documents with session from given URL."""
            logger.info(f"Requesting URL: {url}")

            if not self.__validate_url(url):
                logger.warning(f"Attempted to fetch an invalid URL: {url}, skipping.")
                return None

            async with session.get(url) as response:
                logger.info(f"retrieved with response: {response.status}")

                if response.status != 200:
                    logger.info(
                        f"Failed to fetch {url} with status code: {response.status}, stopping.."
                    )
                    self.running = False
                    return

                return await response.text()

        async with aiohttp.ClientSession() as session:
            while self.url_queue and self.running:
                url = self.url_queue.pop()
                html = await fetch(session, url)

                # If HTML is none, continue.
                # fetch() takes care of logging information.
                if html is None:
                    continue

                self._current_page = html

                self.scraper.document = html
                result = self.scraper.scrape()

                # If there are no links found, stop.
                if len(result["links"]) == 0:
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
