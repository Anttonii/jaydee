import json
import logging

from bs4 import BeautifulSoup

# Setup the scraper specific logger
logger = logging.getLogger('scraper')

VALID_ELEMENTS = ["a", "abbr", "acronym", "address", "area", "b", "base", "bdo", "big", "blockquote", "body", "br", "button", "caption", "cite", "code", "col", "colgroup", "dd", "del", "dfn", "div", "dl", "DOCTYPE", "dt", "em", "fieldset", "form", "h1", "h2", "h3", "h4", "h5", "h6", "head", "html", "hr", "i", "img",
                  "input", "ins", "kbd", "label", "legend", "li", "link", "map", "meta", "noscript", "object", "ol", "optgroup", "option", "p", "param", "pre", "q", "samp", "script", "select", "small", "span", "strong", "style", "sub", "sup", "table", "tbody", "td", "textarea", "tfoot", "th", "thead", "title", "tr", "tt", "ul", "var"]


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

        Args:
            target: the key that will store the resulting elements text after scraping.
                    Do note that this is an unique identifier.
            attributes: an object that contains the scraping attributes
        """
        if not ("id" in attributes or "class_name" in attributes or "element" in attributes):
            raise ValueError(
                "Attributes provide no narrowing of the DOM and are thus invalid.")

        if target == "":
            raise ValueError("Target can not be an emptry string.")

        self._target = target

        self._attribs = {
            "id": None,
            "element": None,
            "class_name": None,
            "child_of": None,
        }

        self._attribs.update(attributes)

    def __getitem__(self, key: str):
        """
        Refers to attributes list.

        rule['id'] is equilevant to rule.attribs['id']

        Args:
            key: the key used for indexing the attributes object

        Returns:
            value indicating the value that corresponds to the key in attribs.
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
                f" - with child rules: {self._attribs['child_of']}"
            ]
        )


class Scraper:
    """
    Scraper takes in the inner HTML document and a list of rules that determine
    what data to scrape from the HTML docuemnt.
    """

    # The inner list of scraper rules and targets.
    rules = []
    targets = []

    def __init__(self, html_doc: str):
        self.document = html_doc
        self.parser = BeautifulSoup(html_doc, "html.parser")

    def add_rule(self, rule: ScraperRule):
        """
        Utility function that adds a rule to the scraper if it is considered valid.

        Args:
            rules: The rules to add to the scraper
        Raises:
            ScraperException: when attempting to add a rule that has the same
                              target as another rule already defined or when a rule is otherwise invalid.
        """
        logging.info(f"Adding rule with target: {rule.target}")

        # TODO: check recursively for child rules elements
        if 'element' in rule.attributes and rule.attributes['element'] not in VALID_ELEMENTS:
            raise ScraperException("Invalid HTML element.")

        if rule.target in self.targets:
            raise ScraperException(
                "Attempting to add a rule with overlapping target with another rule.")

        self.targets.append(rule.target)
        self.rules.append(rule)

    def add_rules(self, rules: list[ScraperRule]):
        """
        Utility function that adds rules to the scraper.

        Args:
            rules: The rules to add to the scraper
        Returns:
            The instance of self with updated list of rules.
        Raises:
            ScraperException: when attempting to add a rule that has the same
                              target as another rule already defined.
        """
        for rule in rules:
            self.add_rule(rule)

        return self

    def from_json(self, json_path: str):
        """
        Import rules from a json file.

        Args:
            json_path: the path to import the file from.

        Returns:
            Instance of self with rules loaded from the json file.
        """
        try:
            with open(json_path) as json_file:
                rules = json.load(json_file)

            for rule in rules:
                self.add_rule(ScraperRule(**rule))

        except Exception as e:
            logger.info(f"Failed to load rules from path: {json_path}.")
            logger.error(e)

        return self

    def scrape(self):
        """
        Scrapes the given HTML document with the provided rule set.

        TODO: Improve error handling

        Returns:
            Dictionary with keys that map to the provided rules targets.
        """
        def build_attribs(attribs: dict[str, str | dict]) -> dict[str, str]:
            """
            Helper method that converts ScraperRules attributes to a BeautifulSoup
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
                    logger.info(f"No data loaded for rule: {rule}")
                    result[rule.target] = ""
                    continue

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
                logger.info(f"No data loaded for rule: {rule}")
                result[rule.target] = ""
                continue

            result[rule.target] = "\n".join(
                [el.get_text().strip() for el in data])

        return result


class ScraperException(Exception):
    """
    Exception type for scraper functions.
    """

    def __init__(self, *args):
        super().__init__(*args)
