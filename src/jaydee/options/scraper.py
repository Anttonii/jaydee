from dataclasses import dataclass


@dataclass(init=False)
class ScraperOptions:
    # Whether or not standardized HTML tags are allowed.
    _allow_unknown_tags: bool

    # Replaces apostrophes and quotes with escape string syntax
    _add_escapes: bool

    def __init__(
        self,
        allow_unknown_tags: bool = False,
        add_escapes: bool = False,
    ):
        self._allow_unknown_tags = allow_unknown_tags
        self._add_escapes = add_escapes
