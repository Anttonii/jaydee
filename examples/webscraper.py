import asyncio

from src.jaydee.scraper import Scraper, ScraperRule
from src.jaydee.webscraper import WebScraper
from src.jaydee.crawler import Crawler, CrawlerOptions


async def main():
    scraper = Scraper().add_rules(
        [
            ScraperRule(
                target="title",
                attributes={
                    "element": "h1",
                    "child_of": {"element": "div", "class_name": "pane-node-title"},
                },
            )
        ]
    )

    webscraper = WebScraper(scraper=scraper)

    async def on_proceed(crawler):
        nonlocal webscraper
        links = crawler.get_links()

        webscraper.add_urls(links)
        result = await webscraper.scrape_pages()
        print(result)

        crawler.stop()

    options = CrawlerOptions(headless=True)
    crawler = Crawler(
        "https://www.jobly.fi/tyopaikat/terveydenhuolto",
        options=options,
        callback=on_proceed,
        child_of={"element": "div", "class_name": "job__logo"},
    )

    async for link in crawler.start():
        print(link)


def start():
    asyncio.run(main())
