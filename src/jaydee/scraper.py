import json
import logging
import os

from .options import ScraperOptions

from bs4 import BeautifulSoup

# Setup the scraper specific logger
logger = logging.getLogger("jd-scraper")

# The default parser to use for scraping data.
DEFAULT_PARSER = "html5lib"

# Valid HTML elements. Used for validating rules.
VALID_ELEMENTS = [
    "a",
    "abbr",
    "acronym",
    "address",
    "area",
    "article",
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
    "main",
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
    A scraper rule contains information about how we want to scrape a HTML document.

    Target is the key for the resulting object in which the scraped values are stored in.

    Attributes constitute how the scraping is done. The scraper looks for
    elements with given class names or ids from the HTML document and stores them into
    the resulting objects target keys.

    Args:
        target: the key that will store the resulting elements text after scraping.
                Do note that this is an unique identifier, two rules with the same target can not be used.
        attributes: an object that contains the scraping attributes such as element, id and class name.
    Raises:
        ValueException when validation of the rule fails.
    """

    def __init__(
        self,
        target: str,
        select: str | None = None,
        attributes: dict[str, str | dict] | None = None,
    ):
        """Constructor"""
        # First validate the rule.
        if attributes is not None:
            self.__validate_rule(attributes)

        if not target or target == "":
            raise ValueError("Target can not be an empty string.")

        self._target = target
        self._select = select

        self._attribs = {
            "id": None,
            "element": None,
            "class_name": None,
            "property": None,
            "child_of": None,
        }

        if attributes is not None:
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
                "Attributes provide no valid scraping of the DOM and are thus invalid.\nMake sure to have at least defined an element or a class name for scraping."
            )

        # Validate children recursively
        if "child_of" in attributes and attributes["child_of"]:
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
                f" - or with select: {self._select}",
            ]
        )


class Scraper:
    """
    Scraper takes in the inner HTML document and a list of rules that determine
    what data to scrape from the HTML document.

    Args:
        html_doc: an optional html document to scrape data from. if left empty, the scraper
                    instance must be initialized later with an html doc before any scraping.
        rules: an optional list of scraper rules to initialize the scraper with.
        options: optionally add your own scraper options.
    """

    def __init__(
        self,
        html_doc: str = None,
        rules: list[ScraperRule] = None,
        options: ScraperOptions = ScraperOptions(),
    ):
        if html_doc is None:
            self._document = None
            self._parser = None
        else:
            self._document = html_doc
            self._parser = BeautifulSoup(html_doc, DEFAULT_PARSER)

        self.rules = {}
        self._options = options

        if rules is not None:
            self.add_rules(rules)

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
                "Attempting to add a rule that has an overlapping target with another rule.",
                rule,
            )

        if rule.attributes is not None:
            self.__validate_html_tag(rule.attributes)

        self.rules[rule.target] = rule

    def __validate_html_tag(self, attributes):
        """Check for valid HTML element."""
        if "element" in attributes:
            if (
                attributes["element"] not in VALID_ELEMENTS
                and not self._options._allow_unknown_tags
            ):
                raise ValueError(
                    f"Invalid HTML element: {attributes['element']}, this error can be omitted by changing allow_unknown_tags in scraper options."
                )

        if "child_of" in attributes and attributes["child_of"]:
            self.__validate_html_tag(attributes["child_of"])

    def add_rules(self, rules: list[ScraperRule]):
        """
        Utility function that adds a list of rules to the scraper.

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
                logger.info("Path does not exists, loading rules from JSON string.")
                rules = json.loads(json_data)
            else:
                with open(json_data) as json_file:
                    rules = json.load(json_file)

            for rule in rules:
                self.add_rule(ScraperRule(**rule))
        except ScraperException as e:
            logger.error(e)
            if e.get_error_rule() is not None:
                logger.error(e.get_error_rule())

        except Exception as e:
            logger.warning(f"Failed to load rules from: {json_data}")
            logger.error(e)

        return self

    def to_json(self, json_path: str, overwrite: bool = False):
        """
        Converts scrapers active rule set into a .json file.

        Args:
            json_path: the path where the json file will be written to.
            overwrite: whether or not to overwrite when the path has a pre-existing file.
        """

        def convert(value):
            return value.replace("_", "") if value != "_attribs" else "attributes"

        if len(self.rules) == 0:
            logger.warning("Can't convert an empty list of rules into a json file.")
            return

        if os.path.exists(json_path) and not overwrite:
            logger.info(
                f"Overwrite flag set to false and path: {json_path} exists, no json file output."
            )
            return

        rules_data = []
        for rule in self.rules.values():
            dict = rule.__dict__
            keymap = {k: convert(k) for k in dict.keys()}
            rules_data.append({nk: dict[ok] for (ok, nk) in keymap.items()})

        try:
            with open(json_path, "w") as file:
                json.dump(rules_data, file)
            logger.info(f"Scraper rules converted to a json file in path: {json_path}")
        except Exception as e:
            logger.error("Error when converting scraper rules to a json file.")
            logger.error(e)

    def scrape(self, document: str = None) -> dict:
        """
        Scrapes the given HTML document with the provided rule set.

        Args:
            document: optionally supply document that then override the current document.

        Returns:
            Dictionary with keys (rules targets) that map to the extracted properties or text.
        """

        def build_attribs(attribs: dict[str, str | dict]) -> dict[str, str]:
            """
            Helper method that converts ScraperRules attributes to a BeautifulSoup
            compatible one.
            """
            attrs = {}

            # If id or class is empty, look for elements that don't have them set.
            if "id" in attribs and attribs["id"]:
                if attribs["id"] != "":
                    attrs["id"] = attribs["id"].split(" ")
                else:
                    attrs["id"] = None

            if "class_name" in attribs and attribs["class_name"]:
                if attribs["class_name"] != "":
                    attrs["class"] = attribs["class_name"].split(" ")
                else:
                    attrs["class"] = None

            return attrs

        if document is not None:
            self.document = document

        result = {}

        if len(self.rules) == 0:
            logger.error("Can't scrape a document with 0 rules set.")
            return result

        if len(self._document) == 0:
            logger.error("Can't scrape an empty document.")
            return result

        for target, rule in self.rules.items():
            result[target] = []

            if rule._select is not None:
                result[target] = [
                    tag.get_text() for tag in self._parser.select(rule._select)
                ]
                continue

            curr = rule["child_of"]
            child_rules = []

            while curr:
                child_rules.append(curr)

                if "child_of" in curr:
                    curr = curr["child_of"]
                else:
                    curr = None

            curr_target = self._parser
            while child_rules:
                child_rule = child_rules.pop()

                # found no child elements, improper rule
                if not curr_target:
                    logger.warning(
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

                curr_target = BeautifulSoup(str(curr_target), DEFAULT_PARSER)

            if not curr_target:
                logger.warning(
                    f"After processing child rules, no data was found for: {rule}"
                )
                continue

            attrs = build_attribs(rule.attributes)

            element = rule["element"]
            if element:
                data = curr_target.find_all(element, attrs=attrs)
            else:
                data = curr_target.find_all(attrs=attrs)

            if len(data) == 0:
                logger.warning(f"No data loaded for rule: {rule}")
                result[target] = []
                continue

            # Check first if we want to parse properties instead of text.
            property = rule["property"]
            if property:
                result[target] = [el[property] for el in data if el.has_attr(property)]
            else:
                result[target] = [el.get_text().strip() for el in data]
                if self._options._add_escapes:
                    result[target] = list(
                        map(lambda x: self.__add_escapes(x), result[target])
                    )

        return result

    def reset(self):
        """
        Resets the inner parser object back to the state of object construction.

        Also clears the list of defined rules.
        """
        self._parser = BeautifulSoup(self._document, DEFAULT_PARSER)
        self.rules = {}

    def __add_escapes(self, text: str) -> str:
        """Adds escapes to single apostrophes"""
        text = text.replace("'", "''")
        text = text.replace('"', '""')
        return text

    @property
    def document(self):
        return self._document

    @document.setter
    def document(self, val):
        self._document = val
        self._parser = BeautifulSoup(val, DEFAULT_PARSER)

    @property
    def options(self):
        return self._options

    @options.setter
    def options(self, val):
        self._options = val


class ScraperException(Exception):
    """
    Exception type for scraper functions.
    """

    def __init__(self, message, rule: ScraperRule | None = None):
        super().__init__(message)

        self.rule = rule

    def get_error_rule(self):
        """
        Returns the error rule that caused the scraper exception.
        """
        return self.rule
