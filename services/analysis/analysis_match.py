from enum import Enum
from typing import TypedDict, Tuple, Dict, Union, List, Optional
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
    #todo: lemma_key obsolete
    lemma_key: Optional[Tuple[str, ...]]
    search_match: Union[FTSTextMatch, FTSRegexMatch]
    found: Dict[str, Union[str, List[Token]]]
