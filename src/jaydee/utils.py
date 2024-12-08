import logging
import random
from urllib.parse import urlparse

logger = logging.getLogger("jd-utils")


# Mock user agent values to use randomly.
DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
]


def parse_base_url(url: str) -> str:
    """
    Parses base part of the url.

    For example given url https://example.com/foo/bar?id=1 return https://example.com

    Args:
        url: url to parse base url from.
    Returns:
        str: the base url of the given url.
    """
    parsed_url = urlparse(url)
    return parsed_url.scheme + "://" + parsed_url.netloc


def validate_url(url: str) -> bool:
    """
    Validates URL to see if it's valid.

    Args:
        url: url to validate
    Returns:
        bool: whether or not the url is valid.
    """
    try:
        parsed_url = urlparse(url)
        return all([parsed_url.scheme, parsed_url.netloc])
    except AttributeError:
        return False


def get_random_user_agent() -> str | None:
    """Returns a random user agent from list of defaults."""
    if len(DEFAULT_USER_AGENTS) == 0:
        logger.warning("No user agents set, will default to Playwrights user agent.")
        return None

    if len(DEFAULT_USER_AGENTS) == 1:
        logger.warning("It's suggested to use more than one user agent.")

    return random.choice(DEFAULT_USER_AGENTS)
