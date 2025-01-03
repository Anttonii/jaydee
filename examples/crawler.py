import asyncio

from src.jaydee.crawlers import LinkCrawler
from src.jaydee.options import CrawlerOptions, WaitForOptions


async def main():
    # on_proceed is called once the crawlers url queue is empty.
    # defining it is optional.
    async def on_proceed(crawler):
        # Add pages after crawler has extracted links.
        crawler.add_url("https://www.reddit.com/r/ProgrammerHumor/")

    # Avoid using wait for idle in real code and instead use a selector.
    wait_for = WaitForOptions(wait_for_idle=True)
    options = CrawlerOptions(headless=True, wait_for_options=wait_for)
    crawler = LinkCrawler(
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
