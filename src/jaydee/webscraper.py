import asyncio
import logging
from copy import deepcopy

from .scraper import Scraper
from .options import WebScraperOptions
from . import utils

from playwright.async_api import async_playwright

logger = logging.getLogger("jd-webscraper")


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
        self.url_queue = []
        self.add_urls(urls)

        self.scraper = scraper
        self.options = options

        self._current_result = {}
        self._total_success = 0
        self._total_failures = 0
        self._total_skipped = 0
        self._total = 0

    async def scrape_pages(self):
        """
        Starts the page scraping coroutine.
        """
        if not self.url_queue:
            logger.error("No URLs in queue, unable to web scrape.")
            return

        async with async_playwright() as pw:
            self._current_result = {
                "results": [],
                "success": 0,
                "failures": 0,
            }

            browser = await pw.chromium.launch()
            contexts = [
                await browser.new_context(
                    user_agent=utils.get_random_user_agent(),
                    viewport={"width": 1920, "height": 1080},
                )
                for _ in range(self.options._pool_size)
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
                        self.total_skipped += 1
                        continue

                    index = (index + 1) % self.options._pool_size

                    context = contexts[index]
                    scraper = scrapers[index]

                    tasks.append(
                        self.__scrape_page_semaphore(context, semaphore, url, scraper)
                    )

                await asyncio.gather(*tasks)

                self.total_success += self.current_result["success"]
                self.total_failures += self.current_result["failures"]
                self.total += (
                    self.total_success + self.total_failures + self.total_skipped
                )

                return self.current_result
            except Exception as e:
                logger.error(
                    "Error occurred in the webscraper page scraping coroutine:"
                )
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
            scraper: instance of a scraper to scrape the page with.
        """
        page = await context.new_page()
        # Trick for attempting to bypass restrictions
        await page.add_init_script("delete Object.getPrototypeOf(navigator).webdriver")
        try:
            logger.info(f"Scraping {url}...")

            await page.goto(url, timeout=self.options._timeout * 1000)
            await self.options._wait_for_options.async_wait_for(page)
            content = await page.content()

            result = scraper.scrape(content)

            self.current_result["results"].append(result)
            self.current_result["success"] += 1
        except Exception as e:
            self.current_result["failures"] += 1

            logger.error(f"Error with scraping url: {url}")
            logger.error(e)
        finally:
            await page.close()

    async def scrape_page(self, url: str):
        """
        Scrapes a web page using the base scraper instance.

        In case of error, returns an empty object.
        """
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True, args=utils.get_chrome_arguments()
            )
            context = await browser.new_context(
                user_agent=utils.get_random_user_agent(),
                viewport={"width": 1920, "height": 1080},
            )
            page = await context.new_page()
            # Trick for attempting to bypass restrictions
            await page.add_init_script(
                "delete Object.getPrototypeOf(navigator).webdriver"
            )
            try:
                if not utils.validate_url(url):
                    logger.warning(
                        f"Attempting to scrape invalid URL: {url}, skipping.."
                    )
                    return {}

                await page.goto(url, timeout=self.options._timeout * 1000)
                await self.options._wait_for_options.async_wait_for(page)

                html = await page.content()
                result = self.scraper.scrape(html)
                result["_content"] = html

                return result
            except Exception as e:
                logger.error(f"Error with scraping url: {url}")
                logger.error(e)
            finally:
                await page.close()
                await browser.close()

    def add_urls(self, urls: list[str]):
        """Adds urls to the list to be scraped. URLs are validated before they are appended."""
        for url in urls:
            if not utils.validate_url(url):
                logger.info(
                    f"Attempting to add invalid URL: {url} to queue, skipping.."
                )
                continue

            self.url_queue.append(url)

    @property
    def current_result(self):
        return self._current_result

    @current_result.setter
    def current_result(self, val):
        self.current_result = val

    @property
    def total_success(self):
        return self._total_success

    @total_success.setter
    def total_success(self, val):
        self._total_success = val

    @property
    def total_failures(self):
        return self._total_failures

    @total_failures.setter
    def total_failures(self, val):
        self._total_failures = val

    @property
    def total(self):
        return self._total

    @total.setter
    def total(self, val):
        self._total = val

    @property
    def total_skipped(self):
        return self._total_skipped

    @total_skipped.setter
    def total_skipped(self, val):
        self._total_skipped = val
