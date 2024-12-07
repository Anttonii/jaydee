import aiohttp
import asyncio

from src.jaydee.scraper import Scraper


async def main():
    async with aiohttp.ClientSession() as session:
        async with await session.get("https://www.example.com") as response:
            scraper = Scraper(html_doc=await response.text()).from_json(
                "examples/example.json"
            )

            result = scraper.scrape()

            for k, v in result.items():
                print(f"{k}: {v}")


def start():
    asyncio.run(main())
