# Jaydee

Crawl websites and scrape HTML documents using a .json file schema.

## Installation

Make sure you have playwright installed with:

```bash
$ pip install playwright
$ playwright install
```

Currently Jaydee runs on chromium so make sure that playwright at least installs that as a webdriver.

Afterwards install Jaydee from PIP:

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
