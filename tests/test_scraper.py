import pytest

from scraper import Scraper, ScraperRule


class TestScraperInstance:
    @pytest.fixture(autouse=True)
    def test_rules(self):
        self.test_rules = [
            ScraperRule(target="title", attributes={
                "element": "div",
                "class_name": "within-class"
            })
        ]

    @pytest.fixture(autouse=True)
    def test_html(self):
        self.test_html = """
        <!DOCTYPE html>
        <html>
        <body>

        <div class="within-class">
            <h1>Heading</h1>
        </div>

        <p>My first paragraph.</p>

        </body>
        </html> 
         """

    def test_scraping(self):
        scraper = Scraper(html_doc=self.test_html).add_rules(self.test_rules)
        result = scraper.scrape()

        # Make sure that rule targets are part of the result.
        for rule in self.test_rules:
            assert rule.target in result

        # Make sure that the gathered value is correct.
        assert result['title'] == "Heading"
