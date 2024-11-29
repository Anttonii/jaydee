import os
import requests

from .scraper import Scraper, ScraperRule


def start():
    offline = False

    rules = [
        ScraperRule("body",
                    attributes={
                        "element": "div",
                        "class_name": "node__content"
                    }),
        ScraperRule(
            "title",
            attributes={
                "element": "h2",
                "child_of": {
                    "element": "div",
                    "class_name": "pane-node-title"
                }
            },
        ),
    ]

    if not offline:
        r = requests.get(
            "https://www.jobly.fi/tyopaikka/director-licensing-iot-2222448")
        scraper = Scraper(html_doc=r.content, rules=rules)
    else:
        html_doc = ''
        with open('/Users/anttoni/programming/jdscraper/data/test.html', 'r') as file:
            html_doc = file.readlines()
        scraper = Scraper(html_doc=html_doc[0], rules=rules)

    result = scraper.scrape()

    for k, v in result.items():
        print(f"{k}: {v}")
