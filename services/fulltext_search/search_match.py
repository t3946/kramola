from dataclasses import dataclass
from typing import List, Optional
from services.utils.regex_pattern import RegexPattern
from services.fulltext_search.token import Token


@dataclass
class SearchMatch:
    """Result of a search match with information about how it was found."""
    tokens: List[Token]
    search_text: Optional[str] = None
    regex_info: Optional[RegexPattern] = None

    def __post_init__(self):
        """Validate that either search_text or regex_info is provided."""
        if self.search_text is None and self.regex_info is None:
            raise ValueError("Either search_text or regex_info must be provided")
