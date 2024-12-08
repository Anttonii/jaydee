# Jaydee

Crawl websites and scrape HTML documents using a .json file schema.

## Installation

```bash
$ pip install jaydee
```

## Usage

More in-depth usage examples can be found in the directory `examples`.

Crawling:
```python
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
```

Scraping:
```python
import requests

from jaydee import Scraper

# Retrieve an HTML document.
r = requests.get("https://example.com")

# Setup the scraper with rules according to a .json file.
scraper = Scraper(html_doc=r.content).from_json("data/rules.json")

# Get a result
result = scraper.scrape()
```

## License

This repository is licensed under the MIT license.
