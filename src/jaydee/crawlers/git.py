from .base import BaseCrawler
from jaydee import utils
from jaydee.options import GitCrawlerOptions

from tempfile import TemporaryDirectory
import logging
import os
import subprocess

# Setup the link crawler specific logger
logger = logging.getLogger("jd-git-crawler")


class GitCrawler(BaseCrawler):
    """
    Git crawler crawls through git repositories and then creates new directories to which
    the repositories are clones to.

    After this process the crawler will go through the cloned repository and store
    all the code related information into the resulting dictionary.
    """

    def __init__(
        self,
        ignore=(".git", ".toml", ".lock", ".png", ".jpg", ".gif", ".gitignore"),
        options=GitCrawlerOptions(),
    ):
        super().__init__()

        # File extensions and directories to ignore when extracting data.
        self._ignore = ignore
        self._options = options

    def extract_from_url(self, url: str) -> dict | None:
        """Extracts information from a repository given a valid clonable URL."""
        assert utils.validate_url(url), "The provided URL must be a valid url."

        # The result of the scraping process.
        result = None

        # In strict mode check for repository validity before scraping.
        if self._options._strict:
            if not self.check_if_valid_repository(url):
                logger.warning("Invalid git repository, skipping..")
                return result

        logger.info(f"Scraping repository from URL: {url}")
        repo_name = url.rstrip("/").split("/")[-1]
        platform = utils.parse_base_url(url)

        with TemporaryDirectory() as temp_dir:
            print(f"Created temporary directory: {temp_dir}")

            try:
                # Clone the repository
                subprocess.run(["git", "clone", url], cwd=temp_dir, check=True)

                # Assume that the directory is empty outside of the cloned repository.
                repo_path = os.path.join(temp_dir, os.listdir(temp_dir)[0])

                file_tree = {}
                for root, _, files in os.walk(repo_path):
                    dir = root.replace(repo_path, "").lstrip("\\")
                    if dir.startswith(self._ignore):
                        continue

                    for file in files:
                        if file.endswith(self._ignore):
                            continue

                        file_path = os.path.join(dir, file)
                        with open(os.path.join(root, file), "r", errors="ignore") as f:
                            file_tree[file_path] = f.read().replace(" ", "")

                result = {
                    "name": repo_name,
                    "content": file_tree,
                    "url": url,
                    "platform": platform,
                }

            except Exception as e:
                logger.error(f"Error when parsing file tree: {e}")
                raise

        logger.info("Finished scraping Github repository.")
        return result

    def check_if_valid_repository(self, url: str) -> bool:
        """Checks if the given url is a valid git repository or not."""
        assert utils.validate_url(url), "The provided URL must be a valid url."

        # Run the list remote to check if the url is a git repository.
        result = subprocess.run(["git", "ls-remote", url])

        # If it returns 0, the url is a valid git repository.
        return result.returncode == 0
