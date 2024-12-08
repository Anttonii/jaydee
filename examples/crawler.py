import asyncio

from src.jaydee.crawler import Crawler


async def main():
    # on_proceed is called once the crawlers url queue is empty.
    # defining it is optional.
    def on_proceed(crawler):
        # Add pages after crawler has extracted links.
        crawler.add_url("https://www.example.com/foo")

    crawler = Crawler(
        "https://www.example.com",
        on_proceed,
    )

    async for link in crawler.start():
        print(link)


def start():
    asyncio.run(main())
