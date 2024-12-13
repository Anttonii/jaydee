# Changelog

## v0.1.3a (13/12/2024)

### Hotfix:

- Faulty scraper attribute handling.

## v0.1.3 (13/12/2024)

### Additions

- Webscraper can now also wait for selectors/states/text.
- Webscraper keeps track of scraping results.
- Scraper has an option to add escape posix sequences to apostrophes and quotes.
- Crawler can wait for some text to be visible before parsing.
- Setting `id` or `class_name` as empty string looks for elements that have no id or class set.
- Added support for selectors in the scraper.

### Changes

- Refactored examples
- Added tests

## v0.1.2 (12/12/2024)

### Additions

- Initial Playwright support.
- Multithreaded web scraping.
- `strict` crawling that keeps the crawler within the base URLs domain.
- Crawler now returns metadata when crawling.

### Changes

- Moved some shared functionality over to `utils.py`

## v0.1.1 (7/12/2024)

### Additions

- Crawler functionality.
- Scraper can be set to scrape specific properties of html tags instead of just raw text.

### Miscellaneous

- Added code examples.
- Added tests.

## v0.1.0 (2/12/2024)

- Scraper core functionality implemented.
- Tests for core functionality implemented.