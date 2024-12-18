import asyncio

from src.jaydee.scraper import Scraper, ScraperRule
from src.jaydee.webscraper import WebScraper
from src.jaydee.crawler import Crawler
from src.jaydee.options import CrawlerOptions


async def main():
    scraper = Scraper().add_rules(
        [
            ScraperRule(
                target="ppg",
                attributes={
                    "element": "p",
                    "class_name": "PlayerSummary_playerStatValue___EDg_",
                },
            )
        ]
    )

    webscraper = WebScraper(scraper=scraper)

    async def on_proceed(crawler):
        crawler.stop()

    options = CrawlerOptions(headless=True, waitForText="5-9 ft")
    crawler = Crawler(
        "https://www.nba.com/stats/players/shooting",
        on_proceed,
        options=options,
        rule=ScraperRule(
            target="links",
            attributes={"element": "a", "child_of": {"element": "tr"}},
        ),
    )

    async for result in crawler.start():
        links = result["links"]
        links = list(map(lambda x: x[0] % 2 == 0, enumerate(links)))

        webscraper.add_urls(links)
        result = await webscraper.scrape_pages()
        print(result)


def start():
    asyncio.run(main())
