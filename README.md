# Jaydee

Scrape HTML documents using a .json file schema.

## Installation

Make sure that Jaydee is recognizable by poetry by adding it to your `pyproject.toml` and afterwards:

```bash
poetry install
```

## Usage

```python
import requests

from jaydee import Scraper

# Retrieve an HTML document.
r = requests.get("https://example.com")

# Setup the scraper with rules according to a .json file.
scraper = Scraper(html_doc=r.content).from_json("data/rules.json")

# Get a result
result = scraper.scrape()
```

## License

This repository is licensed under the MIT license.
