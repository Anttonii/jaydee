import pytest

from unittest.mock import MagicMock

from jaydee.options import WebScraperOptions, MultithreadOptions
from jaydee.webscraper import WebScraper
from jaydee.scraper import Scraper


@pytest.fixture
def mock_scraper():
    scraper = MagicMock(spec=Scraper)
    scraper.scrape.return_value = {"data": "mocked"}
    return scraper


@pytest.fixture
def mock_options():
    return WebScraperOptions(
        timeout=5, retries=3, multithread_options=MultithreadOptions()
    )


@pytest.fixture
def mock_urls():
    return ["https://example.com", "https://test.com"]


@pytest.fixture
def webscraper(mock_scraper, mock_options, mock_urls):
    return WebScraper(scraper=mock_scraper, urls=mock_urls, options=mock_options)


@pytest.mark.asyncio
async def test_add_urls(webscraper):
    valid_url = "https://new-example.com"
    invalid_url = "invalid-url"

    webscraper.add_urls([valid_url, invalid_url])

    assert valid_url in webscraper.url_queue
    assert invalid_url not in webscraper.url_queue
