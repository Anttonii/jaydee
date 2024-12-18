import playwright.async_api as pwa
from playwright.async_api import Page as AsyncPage


class WaitForOptions:
    # If not empty, the crawler waits for selector be present before parsing HTML.
    _wait_for_selector: str | None

    # Whether or not to wait for the network to be idle for half a second before parsing HTML.
    _wait_for_idle: bool

    # If not empty, the crawler waits for equivalent text to be visible on the page.
    _wait_for_text: str | None

    # If not none, waits for given milliseconds
    _wait_for_timeout: int | None

    def __init__(
        self,
        wait_for_selector=None,
        wait_for_idle=False,
        wait_for_text=None,
        wait_for_timeout=None,
    ):
        self._wait_for_idle = wait_for_idle
        self._wait_for_selector = wait_for_selector
        self._wait_for_text = wait_for_text
        self._wait_for_timeout = wait_for_timeout

    async def async_wait_for(self, page: AsyncPage):
        """Invokes the playwright wait for directive based on given options."""
        if self._wait_for_idle:
            await page.wait_for_load_state("networkidle")
        elif self._wait_for_timeout is not None:
            await page.wait_for_timeout(self._wait_for_timeout)
        elif self._wait_for_selector is not None:
            await page.wait_for_selector(self._wait_for_selector)
        elif self._wait_for_text is not None:
            await pwa.expect(
                page.get_by_text(self.options._wait_for_text)
            ).to_be_visible()
