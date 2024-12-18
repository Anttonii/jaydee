import asyncio

from src.jaydee.scraper import Scraper, ScraperRule
from src.jaydee.webscraper import WebScraper
from src.jaydee.options import WebScraperOptions


async def main():
    # Avoid using wait for idle in real code and instead use a selector.
    rules = [
        ScraperRule(
            target="columns",
            attributes={
                "element": "th",
                "child_of": {
                    "element": "table",
                    "id": "",
                },
            },
        ),
        ScraperRule(
            target="rows",
            attributes={
                "element": "td",
                "child_of": {
                    "element": "table",
                    "id": "",
                },
            },
        ),
        ScraperRule(target="success", select="td.result.passed"),
        ScraperRule(target="failures", select="td.failed"),
    ]

    scraper = Scraper(rules=rules)
    options = WebScraperOptions(waitForIdle=True)
    ws = WebScraper(scraper=scraper, options=options)

    result = await ws.scrape_page("https://bot.sannysoft.com/")
    print("Running a detection test.. \n")
    print(result["columns"][0] + " --- " + result["columns"][1])
    print(f"Successes: {len(result["success"])}")
    print(f"Failures: {len(result["failures"])}")


def start():
    asyncio.run(main())
