# read version from installed package
from importlib.metadata import version

__version__ = version("scraper")

from .scraper import Scraper, ScraperRule  # noqa
