from abc import ABC, abstractmethod
from typing import List, Tuple, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from services.fulltext_search.fulltext_search import Token
    from services.fulltext_search.dictionary import TokenDictionary


class BaseSearchStrategy(ABC):
    """Base class for search strategies."""

    @abstractmethod
    def search_token_sequences(
        self,
        source_tokens: 'List[Token]',
        search_tokens: 'List[Token]',
        dictionary: Optional['TokenDictionary'] = None
    ) -> List[Tuple[int, int]]:
        """
        Search token sequences in source text.
        
        Args:
            source_tokens: Tokens from source text
            search_tokens: Tokens from search query
            dictionary: Optional dictionary for faster lookup
            
        Returns:
            List of tuples (start_token_idx, end_token_idx) for matches
        """
        pass
