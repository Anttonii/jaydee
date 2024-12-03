# read version from installed package
from importlib.metadata import version

__version__ = version("jaydee")

from .scraper import Scraper, ScraperRule  # noqa