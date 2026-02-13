from dataclasses import dataclass
from enum import Enum
from typing import TypedDict, Tuple, Dict, Union, List, Optional
from services.tokenization import Token
from services.fulltext_search.search_match import FTSTextMatch, FTSRegexMatch


class AnalysisMatchKind(Enum):
    """Kind of analysis match."""
    WORD = "word"
    PHRASE = "phrase"
    REGEX = "regex"

@dataclass
class AnalysisMatch:
    """Match result enriched with analysis metadata."""
    kind: AnalysisMatchKind
    search_match: Union[FTSTextMatch, FTSRegexMatch]
    found: Dict[str, Union[str, List[Token]]]
    page: Optional[int] = None
