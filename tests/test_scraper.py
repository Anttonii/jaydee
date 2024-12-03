import pytest

from jaydee import Scraper, ScraperRule


@pytest.fixture(scope="class")
def test_rules():
    return [
        ScraperRule(
            target="title",
            attributes={"element": "div", "class_name": "within-class"},
        ),
        ScraperRule(
            target="body",
            attributes={
                "element": "p",
                "child_of": {
                    "element": "div",
                    "class_name": "nested",
                    "child_of": {
                        "element": "div",
                        "class_name": "container",
                    },
                },
            },
        ),
    ]


@pytest.fixture(scope="class")
def test_html():
    return """
    <!DOCTYPE html>
    <html>
    <body>

    <div class="within-class">
        <h1 class="test">Heading</h1>
    </div>

    <div class="container">
        <div class="nested">
            <p>Paragraph</p>
        </div>
    </div>

    </body>
    </html> 
    """


@pytest.fixture(scope="class")
def test_json():
    return """
    [
        {
            "target": "body",
            "attributes": {
                "element": "h1",
                "class_name": "test"
            }
        }
    ]
    """


@pytest.fixture(scope="function")
def scraper(test_html):
    return Scraper(html_doc=test_html)


def test_scraping(scraper, test_rules):
    # Make sure we are running a fresh instance.
    scraper.reset()

    scraper.add_rules(test_rules)
    result = scraper.scrape()

    # Make sure that rule targets are part of the result.
    for rule in test_rules:
        assert rule.target in result

    # Make sure that the scraped value is as expected.
    assert result["title"] == "Heading"
    assert result["body"] == "Paragraph"


def test_rules_from_json_string(scraper, test_json):
    # Make sure we are running a fresh instance.
    scraper.reset()

    scraper.from_json(test_json)
    result = scraper.scrape()

    # Make sure that the scraped value is as expected.
    assert result["body"] == "Heading"


def test_rule_validation():
    # Assert that an exception is raised when a rule is invalid
    with pytest.raises(ValueError, match="Invalid HTML"):
        bad_rules = [  # noqa: F841
            ScraperRule(
                target="title",
                attributes={"element": "dib", "class_name": "content"},
            )
        ]


def test_target_validation():
    # Assert that an exception is raised when no target is defined
    with pytest.raises(ValueError, match="Target can not be"):
        bad_rules = [  # noqa: F841
            ScraperRule(
                target="",
                attributes={"element": "div", "class_name": "content"},
            )
        ]
