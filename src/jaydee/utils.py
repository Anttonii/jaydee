import logging
import random
from urllib.parse import urlparse

from .scraper import ScraperRule, Scraper

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


def parse_domain(url: str) -> str:
    """
    Parses domain name from an URL.

    Args:
        url: url to parse domain from.
    Returns:
        str: the domain of the given url.
    """
    parsed_url = urlparse(url)
    return parsed_url.netloc


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
    """Returns a random user agent."""
    return random.choice(DEFAULT_USER_AGENTS)


def get_chrome_arguments() -> list[str]:
    """Returns chrome arguments optimized for web scraping."""
    return [
        "--disable-features=Translate,OptimizationHints,MediaRouter,DialMediaRouteProvider,CalculateNativeWinOcclusion,InterestFeedContentSuggestions,CertificateTransparencyComponentUpdater,AutofillServerCommunication,PrivacySandboxSettings4,AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-notifications",
        "--disable-extensions",
        "--disable-background-networking",
        "--ignore-certificate-errors",
        "--disable-popup-blocking",
    ]


def rules_to_json(rules: list[ScraperRule], json_path: str):
    """
    Convert a list of scraper rules into a json file.
    """
    scraper = Scraper(rules=rules)
    scraper.to_json(json_path)
