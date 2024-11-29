from bs4 import BeautifulSoup


class ScraperRule:
    """
    Scraper options allows scraper to properly align certain elements
    into correct values in a hashmap.
    """

    def __init__(
        self,
        target: str,
        attributes: dict[str, str | dict],
    ):
        """
        Creates a new scraper rule.

        A scraper rule contains id or a class name and can additionally
        have an element. These values are used to determine scraped values
        in the scraping phase.

        Target is then the resulting post scraping and processing value.
        """
        assert (
            "id" in attributes or "class_name" in attributes or "element" in attributes
        )
        assert target != ""

        self._target = target

        self._attribs = {
            "id": None,
            "element": None,
            "class_name": None,
            "child_of": None,
        }

        self._attribs.update(attributes)

    def __getitem__(self, key):
        """
        Refers to attributes list.

        rule['id'] is equilevant to rule.attribs['id']
        """
        return self._attribs[key]

    @property
    def attributes(self):
        return self._attribs

    @property
    def target(self):
        return self._target

    def __str__(self):
        return "\n".join(
            [
                f"Rule for target: {self.target}",
                f" - looks for element: {self._attribs['element']}",
                f" - with class name: {self._attribs['class_name']}",
                f" - with id: {self._attribs['id']}",
                f" - with children: {self._attribs['child_of']}"
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
        def build_attribs(attribs: dict[str, str | dict]) -> dict[str, str]:
            """
            Helper method that converts rules attributes to a BeautifulSoup
            compatible one.
            """
            attrs = {}

            if "id" in attribs:
                attrs["id"] = attribs["id"]

            if "class_name" in attribs:
                attrs["class"] = attribs["class_name"]

            return attrs

        result = {}

        for rule in self.rules:
            curr = rule['child_of']
            child_rules = []

            while curr:
                child_rules.append(curr)

                if 'child_of' in curr:
                    curr = curr["child_of"]
                else:
                    curr = None

            curr_target = self.parser
            for child_rule in child_rules:
                # found no child elements, improper rule
                if not curr_target:
                    return

                attrs = build_attribs(child_rule)
                if 'element' in child_rule:
                    curr_target = curr_target.find_all(
                        child_rule['element'],
                        attrs=attrs
                    )
                else:
                    curr_target = curr_target.find_all(attrs=attrs)

                curr_target = BeautifulSoup(str(curr_target), "html.parser")

            attrs = build_attribs(rule.attributes)

            if rule["element"]:
                data = curr_target.find_all(rule["element"], attrs=attrs)
            else:
                data = curr_target.find_all(attrs=attrs)

            if len(data) == 0:
                print(f"Failed to load data for rule: {rule}")
                return

            result[rule.target] = [el.get_text().strip() for el in data]

        return result
