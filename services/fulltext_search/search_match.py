from abc import ABC
from dataclasses import dataclass
from typing import List
from services.utils.regex_pattern import RegexPattern
from services.fulltext_search.token import Token


@dataclass
class FTSMatch(ABC):
    """Base class for fulltext search match results."""
    tokens: List[Token]
    start_token_idx: int
    end_token_idx: int


@dataclass
class FTSTextMatch(FTSMatch):
    """Result of a text-based fulltext search match."""
    search_text: str


@dataclass
class FTSRegexMatch(FTSMatch):
    """Result of a regex-based fulltext search match."""
    regex_info: RegexPattern
