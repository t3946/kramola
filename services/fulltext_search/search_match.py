from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from services.fulltext_search.phrase import Phrase
from services.fulltext_search.token import Token
from services.utils.regex_pattern import RegexPattern


@dataclass
class FTSMatch(ABC):
    """Base class for fulltext search match results."""
    tokens: List[Token]  # found tokens sequence
    start_token_idx: int  # found tokens sequence start
    end_token_idx: int  # found tokens sequence end

    @abstractmethod
    def get_search_str(self) -> str:
        pass


@dataclass
class FTSTextMatch(FTSMatch):
    """Result of a text-based fulltext search match."""
    search_phrase: Phrase

    def get_search_str(self) -> str:
        return self.search_phrase.phrase


@dataclass
class FTSRegexMatch(FTSMatch):
    """Result of a regex-based fulltext search match."""
    regex_info: RegexPattern

    def get_search_str(self) -> str:
        return '"' + self.regex_info.pattern_name + '"'
