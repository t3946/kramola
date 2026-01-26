from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List
from services.utils.regex_pattern import RegexPattern
from services.fulltext_search.token import Token


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
    search_text: str

    def get_search_str(self) -> str:
        return self.search_text


@dataclass
class FTSRegexMatch(FTSMatch):
    """Result of a regex-based fulltext search match."""
    regex_info: RegexPattern

    def get_search_str(self) -> str:
        return '"' + self.regex_info.pattern_name + '"'
