import asyncio

from src.jaydee.scraper import Scraper, ScraperRule
from src.jaydee.webscraper import WebScraper
from src.jaydee.crawlers import LinkCrawler
from src.jaydee.options import LinkCrawlerOptions


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

    options = LinkCrawlerOptions(headless=True)
    crawler = LinkCrawler(
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
