import asyncio
import time

from src.jaydee.crawlers import LinkCrawler
from src.jaydee.options import CrawlerOptions, WaitForOptions, MultithreadOptions


# A multithreaded crawler
async def main():
    # on_proceed is called once the crawlers url queue is empty.
    # defining it is optional.
    async def on_proceed(crawler):
        # Add pages after crawler has extracted links.
        crawler.add_url("https://www.reddit.com/r/ProgrammerHumor/")
        crawler.add_url("https://www.reddit.com/r/Programming/")
        crawler.add_url("https://www.reddit.com/r/wallstreetbets/")
        crawler.add_url("https://www.reddit.com/r/programminghorror/")
        crawler.add_url("https://www.reddit.com/r/adventofcode/")
        crawler.add_url("https://www.reddit.com/r/csMajors/")
        crawler.add_url("https://www.reddit.com/r/computerscience/")

    # Avoid using wait for idle in real code and instead use a selector.
    wait_for = WaitForOptions(wait_for_idle=True)
    mt_options = MultithreadOptions(pool_size=3, max_concurrent_tasks=1)
    options = CrawlerOptions(
        headless=True,
        multithreaded=True,
        wait_for_options=wait_for,
        multithread_options=mt_options,
    )
    crawler = LinkCrawler(
        "https://www.reddit.com",
        on_proceed,
        options=options,
        child_of={"element": "article"},
    )

    t = time.process_time()
    async for result in crawler.start():
        print(f"Metadata: {result["metadata"]}")
        print(f"Links found: {result["links"]}")
        elapsed_time = time.process_time() - t

        print(f"Result took: {elapsed_time}.")
        t = time.process_time()


def start():
    asyncio.get_event_loop().run_until_complete(main())
