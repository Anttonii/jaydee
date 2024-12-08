import asyncio

from src.jaydee.crawler import Crawler, CrawlerOptions


async def main():
    # on_proceed is called once the crawlers url queue is empty.
    # defining it is optional.
    def on_proceed(crawler):
        # Add pages after crawler has extracted links.
        crawler.add_url("https://www.reddit.com/r/ProgrammerHumor/")

    options = CrawlerOptions(headless=True, waitForIdle=True)
    crawler = Crawler(
        "https://www.reddit.com",
        on_proceed,
        options=options,
        child_of={"element": "art"},
    )

    async for link in crawler.start():
        print(link)


def start():
    asyncio.run(main())
