import asyncio

from src.jaydee.crawler import Crawler, CrawlerOptions


async def main():
    # on_proceed is called once the crawlers url queue is empty.
    # defining it is optional.
    async def on_proceed(crawler):
        # Add pages after crawler has extracted links.
        crawler.add_url("https://www.reddit.com/r/ProgrammerHumor/")

    # Avoid using wait for idle in real code and instead use a selector.
    options = CrawlerOptions(headless=True, waitForIdle=True)
    crawler = Crawler(
        "https://www.reddit.com",
        on_proceed,
        options=options,
        child_of={"element": "article"},
    )

    async for result in crawler.start():
        print(f"Metadata: {result["metadata"]}")
        print(f"Links found: {result["links"]}")


def start():
    asyncio.run(main())
