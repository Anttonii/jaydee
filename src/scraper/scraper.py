from bs4 import BeautifulSoup


class ScraperRule:
    """
    Scraper options allows scraper to properly align certain elements
    into correct values in a hashmap.
    """

    def __init__(
        self,
        target: str,
        attributes: dict[str, str],
        child_of: dict[str, str] = None,
    ):
        """
        Creates a new scraper rule.

        A scraper rule contains id or a class name and can additionally
        have an element. These values are used to determine scraped values
        in the scraping phase.

        Target is then the resulting post scraping and processing value.
        """
        assert "id" in attributes or "class_name" in attributes
        assert target != ""

        self._target = target

        self._attribs = {
            "id": None,
            "element": None,
            "class_name": None,
        }

        self._attribs.update(attributes)
        self._child_of = child_of

    def __getitem__(self, key):
        """
        Refers to attributes list.

        rule['id'] is equilevant to rule.attribs['id']
        """
        return self.attribs[key]

    @property
    def target(self):
        return self._target

    @property
    def child_of(self):
        return self._child_of

    def __str__(self):
        return "/n".join(
            [
                f"Rule for target: {self.target}"
                f" - looks for element: {self.attribs['element']}"
                f" - with class name: {self.attribs['class_name']}"
                f" - with id: {self.attribs['id']}"
            ]
        )


class Scraper:
    """
    Scraper takes in the inner HTML document and scraper information
    according to the rule set it's given.
    """

    # The inner list of scraper rules.
    rules = []

    def __init__(self, html_doc: str, rules: list[ScraperRule]):
        self.document = html_doc
        self.parser = BeautifulSoup(html_doc, "html.parser")

        self.rules = rules

    def scrape(self):
        """
        Scrapes the given HTML document with the provided rule set.
        """
        result = {}

        for rule in self.rules:
            attrs = {}

            if rule["id"]:
                attrs["id"] = rule["id"]

            if rule["class_name"]:
                attrs["class"] = rule["class_name"]

            # TODO: Check whether or not rule is a child of rule.

            if rule["element"]:
                data = self.parser.find_all(rule["element"], attrs=attrs)
            else:
                data = self.parser.find_all(attrs=attrs)

            if len(data) == 0:
                print(f"Failed to load data for rule: {rule}")

            result[rule.target] = [el.get_text().strip() for el in data]

        return result
