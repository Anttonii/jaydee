import json
import logging
import os

from bs4 import BeautifulSoup

# Setup the scraper specific logger
logger = logging.getLogger("jd-scraper")

# Valid HTML elements. Used for validating rules.
VALID_ELEMENTS = [
    "a",
    "abbr",
    "acronym",
    "address",
    "area",
    "b",
    "base",
    "bdo",
    "big",
    "blockquote",
    "body",
    "br",
    "button",
    "caption",
    "cite",
    "code",
    "col",
    "colgroup",
    "dd",
    "del",
    "dfn",
    "div",
    "dl",
    "DOCTYPE",
    "dt",
    "em",
    "fieldset",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "head",
    "html",
    "hr",
    "i",
    "img",
    "input",
    "ins",
    "kbd",
    "label",
    "legend",
    "li",
    "link",
    "map",
    "meta",
    "noscript",
    "object",
    "ol",
    "optgroup",
    "option",
    "p",
    "param",
    "pre",
    "q",
    "samp",
    "script",
    "select",
    "small",
    "span",
    "strong",
    "style",
    "sub",
    "sup",
    "table",
    "tbody",
    "td",
    "textarea",
    "tfoot",
    "th",
    "thead",
    "title",
    "tr",
    "tt",
    "ul",
    "var",
]


class ScraperRule:
    """
    Scraper rules assign
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
        Raises:
            ValueException when validation of the rule fails.
        """
        # First validate the rule.
        self.__validate_rule(attributes)

        if not target or target == "":
            raise ValueError("Target can not be an emptry string.")

        self._target = target

        self._attribs = {
            "id": None,
            "element": None,
            "class_name": None,
            "property": None,
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

    def __validate_rule(self, attributes: dict[str, str | dict]):
        """
        Utility function that validates rule. An invalid rule can't be used for scraping.

        For example a rule with a defined element that is not a valid HTML element tag would be an invalid rule.

        Args:
            attributes: the attributes passed in the constructor
        Raises:
            ValueException: when a rule is found to be invalid.
        """
        if not (
            "id" in attributes
            or "class_name" in attributes
            or "element" in attributes
            or "property" in attributes
        ):
            raise ValueError(
                "Attributes provide no valid scraping of the DOM and are thus invalid.\nMake sure to have at least defined an element or a class for scraping."
            )

        if "element" in attributes:
            if attributes["element"] not in VALID_ELEMENTS:
                raise ValueError(f"Invalid HTML element: {attributes['element']}")

        # Validate children recursively
        if "child_of" in attributes:
            self.__validate_rule(attributes["child_of"])

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
                f" - with child rules: {self._attribs['child_of']}",
            ]
        )


class Scraper:
    """
    Scraper takes in the inner HTML document and a list of rules that determine
    what data to scrape from the HTML docuemnt.
    """

    # The inner dictionary of rules. Keys here are target values of rules.
    rules = {}

    def __init__(self, html_doc: str):
        """
        Initializes the scraper instance.

        Args:
            html_doc: the html document to scrape data from.
        """
        self.document = html_doc
        self.parser = BeautifulSoup(html_doc, "html.parser")

    def add_rule(self, rule: ScraperRule):
        """
        Utility function that adds a rule to the scraper.

        Args:
            rules: The rules to add to the scraper
        Raises:
            ScraperException: when attempting to add a rule that has the same
                              target as another rule already defined or when a rule is otherwise invalid.
        """
        logging.info(f"Adding rule with target: {rule.target}")

        if rule.target in self.rules:
            raise ScraperException(
                "Attempting to add a rule with overlapping target with another rule."
            )

        self.rules[rule.target] = rule

    def add_rules(self, rules: list[ScraperRule]):
        """
        Utility function that adds a list ofrules to the scraper.

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

    def from_json(self, json_data: str):
        """
        Import rules from a JSON file or a JSON string.

        Args:
            json_data: the path or the json string to import the JSON data from.

        Returns:
            Instance of self with rules loaded from the given JSON object.
        """
        try:
            # check if the path exists, if not consider the string to be a valid json.
            if not os.path.exists(json_data):
                rules = json.loads(json_data)
            else:
                with open(json_data) as json_file:
                    rules = json.load(json_file)

            for rule in rules:
                self.add_rule(ScraperRule(**rule))

        except Exception as e:
            logger.info(f"Failed to load rules from: {json_data}")
            logger.error(e)

        return self

    def scrape(self):
        """
        Scrapes the given HTML document with the provided rule set.

        TODO: Improve error handling

        Returns:
            Dictionary with keys (rules targets) that map to the extracted properties or text.
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

        if len(self.rules) == 0:
            logger.error("Can't scrape a document with 0 rules set.")
            return result

        for target, rule in self.rules.items():
            result[target] = []

            curr = rule["child_of"]
            child_rules = []

            while curr:
                child_rules.append(curr)

                if "child_of" in curr:
                    curr = curr["child_of"]
                else:
                    curr = None

            curr_target = self.parser
            while child_rules:
                child_rule = child_rules.pop()

                # found no child elements, improper rule
                if not curr_target:
                    logger.info(
                        f"No data loaded for rule: {rule} in child rule: {child_rule}"
                    )
                    break

                attrs = build_attribs(child_rule)
                if "element" in child_rule:
                    curr_target = curr_target.find_all(
                        child_rule["element"], attrs=attrs
                    )
                else:
                    curr_target = curr_target.find_all(attrs=attrs)

                curr_target = BeautifulSoup(str(curr_target), "html.parser")

            if not curr_target:
                logger.warning(
                    f"After processing child rules, no data was found for: {rule}"
                )
                continue

            attrs = build_attribs(rule.attributes)

            if rule["element"]:
                data = curr_target.find_all(rule["element"], attrs=attrs)
            else:
                data = curr_target.find_all(attrs=attrs)

            if len(data) == 0:
                logger.warning(f"No data loaded for rule: {rule}")
                continue

            # Check first if we want to parse properties instead of text.
            if rule["property"]:
                property = rule["property"]

                result[target] = [el[property] for el in data if el.has_attr(property)]
            else:
                result[target] = "\n".join([el.get_text().strip() for el in data])

        return result

    def reset(self):
        """
        Resets the inner parser object back to the state of object construction.

        Also clears the list of rules defined.
        """
        self.parser = BeautifulSoup(self.document, "html.parser")
        self.rules = {}


class ScraperException(Exception):
    """
    Exception type for scraper functions.
    """

    def __init__(self, *args):
        super().__init__(*args)
