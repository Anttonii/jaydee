import requests

from .scraper import Scraper, ScraperRule


def start():
    r = requests.get("https://www.jobly.fi/tyopaikka/director-licensing-iot-2222448")

    rules = [
        ScraperRule("body", element="div", class_name="node__content"),
        ScraperRule(
            "title",
            element="h2",
        ),
    ]

    scraper = Scraper(html_doc=r.content, rules=rules)
    result = scraper.scrape()
    print(result["body"])
