import pytest

from jaydee.crawlers import LinkCrawler
from jaydee.scraper import ScraperRule


@pytest.fixture
def valid_url():
    return "https://example.com"


@pytest.fixture
def mock_child_of():
    return None  # Replace with a mock or actual object if needed


def test_add_url(valid_url):
    crawler = LinkCrawler(valid_url, None)
    new_url = "https://example.com/new-page"
    crawler.add_url(new_url)

    assert new_url in crawler.url_queue
    assert new_url in crawler.seen_urls

    # Test adding again
    crawler.add_url(new_url)

    # Shouldn't show up in the queue.
    assert len(crawler.url_queue) == 2
    assert len(crawler.seen_urls) == 2


def test_initialization(valid_url, mock_child_of):
    crawler = LinkCrawler(valid_url, None, child_of=mock_child_of)

    assert crawler.base_url == "https://example.com"
    assert crawler.url_queue == [valid_url]
    assert isinstance(crawler.rules, list)
    assert isinstance(crawler.rules[0], ScraperRule)
