import asyncio
import logging
from copy import deepcopy
from dataclasses import dataclass

from .scraper import Scraper
from . import utils

from playwright.async_api import async_playwright

logger = logging.getLogger("jd-webscraper")


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

    def __init__(
        self,
        timeout: int = 2,
        retries: int = 5,
        pool_size: int = 3,
        max_concurrent_tasks: int = 8,
    ):
        self._timeout = timeout
        self._retries = retries
        self._pool_size = pool_size
        self._max_concurrent_tasks = max_concurrent_tasks


class WebScraper:
    """
    Webscraper allows scraping websites with given scraping rules and works concurrently.
    """

    def __init__(
        self,
        scraper: Scraper,
        urls: list[str] = [],
        options: WebScraperOptions = WebScraperOptions(),
    ):
        self.url_queue = urls
        self.scraper = scraper
        self.options = options
        self.results = []

    async def start(self):
        """
        Starts the web scraping coroutine.
        """
        if not self.url_queue:
            logger.error("No URLs in queue, unable to web scrape.")
            return

        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            contexts = [
                await browser.new_context() for _ in range(self.options._pool_size)
            ]
            scrapers = [deepcopy(self.scraper) for _ in range(self.options._pool_size)]
            semaphore = asyncio.Semaphore(self.options._max_concurrent_tasks)

            try:
                index = -1
                tasks = []
                while self.url_queue:
                    url = self.url_queue.pop()

                    if not utils.validate_url(url):
                        logger.warning(
                            f"Attempting to scrape invalid URL: {url}, skipping.."
                        )
                        continue

                    index = (index + 1) % self.options._pool_size

                    context = contexts[index]
                    scraper = scrapers[index]

                    tasks.append(
                        self.__scrape_page_semaphore(context, semaphore, url, scraper)
                    )
                await asyncio.gather(*tasks)
                print(self.results)
            except Exception as e:
                logger.error("Error in the webscraper start coroutine:")
                logger.error(e)
            finally:
                for context in contexts:
                    await context.close()
                await browser.close()

    async def __scrape_page_semaphore(self, context, semaphore, url, scraper):
        """Uses AsyncIOs semaphore for resource management."""
        async with semaphore:
            await self.__scrape_page_from_pool(context, url, scraper)

    async def __scrape_page_from_pool(self, context, url, scraper):
        """
        Scrape a webpage using a provided browser context.

        Args:
            context: browser context provided by Playwright.
            url: URL of the webpage to scrape.
        """
        page = await context.new_page()
        try:
            logger.info(f"Scraping {url}...")
            await page.goto(url, timeout=self.options._timeout * 1000)
            content = await page.content()

            scraper.document = content
            result = scraper.scrape()
            self.results.append(result)
        except Exception as e:
            logger.error(f"Error with scraping url: {url}")
            logger.error(e)
        finally:
            await page.close()
            return {}

    async def scrape_page(self, url):
        """
        Scrapes a web page using the base scraper instance.

        In case of error, returns an empty object.
        """
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=False)
            context = await browser.new_context(
                user_agent=utils.get_random_user_agent(),
                viewport={"width": 1920, "height": 1080},
            )
            page = await context.new_page()
            try:
                if not utils.validate_url(url):
                    logger.warning(
                        f"Attempting to scrape invalid URL: {url}, skipping.."
                    )
                    return {}

                await page.goto(url, timeout=self.options._timeout * 1000)
                html = await page.content()

                self.scraper.document = html
                result = self.scraper.scrape()
                return result
            except Exception as e:
                logger.error(f"Error with scraping url: {url}")
                logger.error(e)
            finally:
                await browser.close()
                return {}

    def add_urls(self, urls: list[str]):
        """Adds urls to the list to be scraped."""
        self.url_queue += urls
