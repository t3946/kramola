from enum import Enum
from typing import TypedDict, Tuple, Dict, Union, List
from services.fulltext_search.token import Token
from services.fulltext_search.search_match import FTSTextMatch, FTSRegexMatch


class AnalysisMatchKind(Enum):
    """Kind of analysis match."""
    WORD = "word"
    PHRASE = "phrase"
    REGEX = "regex"


class AnalysisMatch(TypedDict):
    """Match result enriched with analysis metadata."""
    kind: AnalysisMatchKind
    lemma_key: Tuple[str, ...]
    search_match: Union[FTSTextMatch, FTSRegexMatch]
    found: Dict[str, Union[str, List[Token]]]
