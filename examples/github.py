import asyncio

from src.jaydee.crawlers import GitCrawler


async def main():
    crawler = GitCrawler()

    result = crawler.extract_from_url(url="https://github.com/Anttonii/jaydee")
    print(result)


def start():
    asyncio.run(main())
