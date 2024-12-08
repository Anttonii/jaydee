# read version from installed package
from importlib.metadata import version

__version__ = version("jaydee")

from .scraper import Scraper, ScraperRule, ScraperException, ScraperOptions  # noqa
from .crawler import Crawler, CrawlerOptions  # noqa
