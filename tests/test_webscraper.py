import pytest

from unittest.mock import AsyncMock, MagicMock

from jaydee.options import WebScraperOptions, WaitForOptions, MultithreadOptions
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


@pytest.fixture
def mock_playwright(mocker):
    mock_pw = mocker.patch("jaydee.webscraper.async_playwright", autospec=True)
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()

    mock_pw.return_value.__aenter__.return_value.chromium.launch.return_value = (
        mock_browser
    )
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page

    return {
        "mock_pw": mock_pw,
        "mock_browser": mock_browser,
        "mock_context": mock_context,
        "mock_page": mock_page,
    }


@pytest.mark.asyncio
async def test_scrape_pages_success(webscraper, mock_playwright):
    mock_pw = mock_playwright
    mock_page = mock_pw["mock_page"]

    mock_page.content.return_value = "<html>Mock HTML</html>"

    result = await webscraper.scrape_pages()

    assert result["success"] == len(result["results"])
    assert result["failures"] == 0


@pytest.mark.asyncio
async def test_scrape_pages_with_failures(webscraper, mock_playwright):
    mock_pw = mock_playwright
    mock_page = mock_pw["mock_page"]

    mock_page.goto.side_effect = [None, Exception("Mock Failure")]
    mock_page.content.return_value = "<html>Mock HTML</html>"

    result = await webscraper.scrape_pages()

    assert result["success"] == 1
    assert result["failures"] == 1


@pytest.mark.asyncio
async def test_add_urls(webscraper):
    valid_url = "https://new-example.com"
    invalid_url = "invalid-url"

    webscraper.add_urls([valid_url, invalid_url])

    assert valid_url in webscraper.url_queue
    assert invalid_url not in webscraper.url_queue


@pytest.mark.asyncio
async def test_wait_for_idle_option(webscraper, mock_playwright):
    webscraper.options._wait_for_options = WaitForOptions()
    webscraper.options._wait_for_options._wait_for_idle = True
    mock_pw = mock_playwright
    mock_page = mock_pw["mock_page"]

    await webscraper.scrape_pages()
    mock_page.wait_for_load_state.assert_called_with("networkidle")


@pytest.mark.asyncio
async def test_wait_for_selector_option(webscraper, mock_playwright):
    webscraper.options._wait_for_options = WaitForOptions()
    webscraper.options._wait_for_options._wait_for_selector = "#mock-selector"
    mock_pw = mock_playwright
    mock_page = mock_pw["mock_page"]

    await webscraper.scrape_pages()
    mock_page.wait_for_selector.assert_called_with("#mock-selector")


@pytest.mark.asyncio
async def test_scrape_page_individual(webscraper, mock_playwright):
    mock_pw = mock_playwright
    mock_page = mock_pw["mock_page"]

    mock_page.content.return_value = "<html>Mock HTML</html>"
    url = "https://example.com"

    result = await webscraper.scrape_page(url)

    assert result["_content"] == "<html>Mock HTML</html>"
    webscraper.scraper.scrape.assert_called_with("<html>Mock HTML</html>")
