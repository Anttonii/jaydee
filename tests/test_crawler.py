import pytest

# from unittest.mock import AsyncMock, patch

from jaydee import Crawler
from jaydee import ScraperRule


@pytest.fixture
def valid_url():
    return "https://example.com"


@pytest.fixture
def invalid_url():
    return "htp:/invalid-url"


@pytest.fixture
def mock_child_of():
    return None  # Replace with a mock or actual object if needed


def test_validate_url(valid_url, invalid_url):
    crawler = Crawler(valid_url, None)
    assert crawler._Crawler__validate_url(valid_url) is True
    assert crawler._Crawler__validate_url(invalid_url) is False


def test_parse_base_url(valid_url):
    crawler = Crawler(valid_url, None)
    base_url = crawler._Crawler__parse_base_url(valid_url)
    assert base_url == "https://example.com"


def test_add_url(valid_url):
    crawler = Crawler(valid_url, None)
    new_url = "https://example.com/new-page"
    crawler.add_url(new_url)

    assert new_url in crawler.url_queue
    assert new_url in crawler.seen_urls


def test_initialization(valid_url, mock_child_of):
    crawler = Crawler(valid_url, None, child_of=mock_child_of)

    assert crawler.base_url == "https://example.com"
    assert crawler.url_queue == [valid_url]
    assert isinstance(crawler.rules, list)
    assert isinstance(crawler.rules[0], ScraperRule)


# @pytest.mark.asyncio
# async def test_start_with_mocked_scraper(valid_url):
#     mock_html = "<html><a href='/link1'>Link</a></html>"
#     mock_scraper_result = {"links": ["/link1"]}

#     with (
#         patch("aiohttp.ClientSession.get") as mock_get,
#         patch("crawler.Scraper") as MockScraper,
#     ):
#         # Mock the HTTP response
#         mock_get.return_value.__aenter__.return_value.text.return_value = mock_html
#         mock_get.return_value.__aenter__.return_value.status = 200

#         # Mock the Scraper behavior
#         mock_scraper_instance = MockScraper.return_value
#         mock_scraper_instance.add_rules.return_value = mock_scraper_instance
#         mock_scraper_instance.scrape.return_value = mock_scraper_result

#         crawler = Crawler(valid_url)
#         crawler.add_url(valid_url)

#         async for urls in crawler.start():
#             assert urls == ["https://example.com/link1"]


# @pytest.mark.asyncio
# async def test_start_skips_seen_urls(valid_url):
#     crawler = Crawler(valid_url)
#     crawler.seen_urls.add(valid_url)

#     with patch("aiohttp.ClientSession.get") as mock_get:
#         mock_get.return_value.__aenter__.return_value.text = AsyncMock()

#         async for _ in crawler.start():
#             pass

#         mock_get.assert_not_called()
