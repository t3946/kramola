from dataclasses import dataclass
from typing import List
from services.utils.regex_pattern import RegexPattern
from services.fulltext_search.token import Token


@dataclass
class SearchMatch:
    """Base class for search match results."""
    tokens: List[Token]
    start_token_idx: int
    end_token_idx: int


@dataclass
class TextSearchMatch(SearchMatch):
    """Result of a text-based search match."""
    search_text: str


@dataclass
class RegexSearchMatch(SearchMatch):
    """Result of a regex-based search match."""
    regex_info: RegexPattern
