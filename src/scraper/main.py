import requests

from .scraper import Scraper


def start():
    offline = True

    if not offline:
        r = requests.get(
            "https://www.jobly.fi/tyopaikka/director-licensing-iot-2222448")
        scraper = Scraper(html_doc=r.content).from_json("data/rules.json")

        # Store for offline use
        with open('data/test.html', 'w+') as output:
            output.write(str(r.content, encoding="utf-8"))
    else:
        html_doc = ''
        with open('data/test.html', 'r') as file:
            html_doc = file.readlines()
        html_doc = "".join(html_doc)
        scraper = Scraper(html_doc=html_doc).from_json("data/rules.json")

    result = scraper.scrape()

    for k, v in result.items():
        print(f"{k}: {v}")
