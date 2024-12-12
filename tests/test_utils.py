import pytest

from jaydee import utils


@pytest.fixture
def valid_url():
    return "https://example.com"


@pytest.fixture
def invalid_url():
    return "htp:/invalid-url"


def test_validate_url(valid_url, invalid_url):
    assert utils.validate_url(valid_url) is True
    assert utils.validate_url(invalid_url) is False


def test_parse_base_url(valid_url):
    base_url = utils.parse_base_url(valid_url)
    assert base_url == "https://example.com"
