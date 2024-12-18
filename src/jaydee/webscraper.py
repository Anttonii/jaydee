import asyncio
import logging
from copy import deepcopy

from .scraper import Scraper
from .options import WebScraperOptions
from . import utils

from playwright.async_api import async_playwright

logger = logging.getLogger("jd-webscraper")


class BrowserInstance:
    def __init__(self, scraper, max_concurrent_tasks, wait_for_options):
        self.scraper = scraper
        self.max_concurrent_tasks = max_concurrent_tasks
        self.semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        self.wait_for_options = wait_for_options

        self.pw_context = None
        self.browser = None
        self.browser_context = None

    async def setup(self):
        """Sets up the browser instance"""
        self.pw_context = await async_playwright().start()
        self.browser = await self.pw_context.chromium.launch(headless=True)

        self.browser_context = await self.browser.new_context(
            user_agent=utils.get_random_user_agent(),
            viewport={"width": 1920, "height": 1080},
        )

        return self

    async def clean_up(self):
        """Closes all playwright related instances."""
        await self.browser_context.close()

        await self.browser.close()
        await self.pw_context.stop()

    async def scrape(self, url):
        """Scrapes the given url with inner scraper object."""
        async with self.semaphore:
            page = await self.browser_context.new_page()

            # Trick for attempting to bypass restrictions
            await page.add_init_script(
                "delete Object.getPrototypeOf(navigator).webdriver"
            )

            logger.info(f"Scraping {url}...")
            await page.goto(url, timeout=5000)
            await self.wait_for_options.async_wait_for(page)

            content = await page.content()
            result = self.scraper.scrape(content)

            await page.close()
            return result


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

        self.browser_instances = []

    async def create_browser_instance(self):
        """
        Creates a persistent browser instance.

        Remember to call quit after done scraping to clean up all browser instances.
        """
        if len(self.browser_instances) > self.options._multithread_options._pool_size:
            logger.error(
                "Attempting to create too many browser instances, this is capped by the pool_size multithreading option."
            )
            return

        browser = await BrowserInstance(
            scraper=deepcopy(self.scraper),
            max_concurrent_tasks=self.options._multithread_options._max_concurrent_tasks,
            wait_for_options=self.options._wait_for_options,
        ).setup()

        self.browser_instances.append(browser)

    async def start(self):
        """Starts a webscraper instance by creating underlying Playwright instances."""
        for _ in range(self.options._multithread_options._pool_size):
            await self.create_browser_instance()

    async def quit(self):
        """
        Stops all playwright instances and cleans up.
        """
        for instance in self.browser_instances:
            await instance.clean_up()

        self.browser_instances = []

    async def scrape_pages(self):
        """
        Starts the page scraping coroutine.
        """
        if not self.url_queue:
            logger.error("No URLs in queue, unable to web scrape.")
            return

        if len(self.browser_instances) == 0:
            self.start()

        self._current_result = {
            "results": [],
            "success": 0,
            "failures": 0,
        }

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

                index = (index + 1) % self.options._multithread_options._pool_size
                instance = self.browser_instances[index]

                tasks.append(self.__scrape_page_from_pool(instance, url))

            await asyncio.gather(*tasks)

            self.total_success += self.current_result["success"]
            self.total_failures += self.current_result["failures"]
            self.total += self.total_success + self.total_failures + self.total_skipped

            return self.current_result
        except Exception as e:
            logger.error("Error occurred in the webscraper page scraping coroutine:")
            logger.error(e)

    async def __scrape_page_from_pool(self, instance, url):
        """
        Scrape a webpage using a provided browser context.

        Args:
            context: browser context provided by Playwright.
            url: URL of the webpage to scrape.
            scraper: instance of a scraper to scrape the page with.
        """
        try:
            result = await instance.scrape(url)

            self.current_result["results"].append(result)
            self.current_result["success"] += 1
        except Exception as e:
            self.current_result["failures"] += 1

            logger.error(f"Error with scraping url: {url}")
            logger.error(e)

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
