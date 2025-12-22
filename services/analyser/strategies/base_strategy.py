from abc import ABC, abstractmethod
from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from services.analyser.fulltext_search import Token


class BaseSearchStrategy(ABC):
    """Base class for search strategies."""

    @abstractmethod
    def search_token_sequences(
        self,
        source_tokens: 'List[Token]',
        search_tokens: 'List[Token]'
    ) -> List[Tuple[int, int]]:
        """
        Search token sequences in source text.
        
        Args:
            source_tokens: Tokens from source text
            search_tokens: Tokens from search query
            
        Returns:
            List of tuples (start_token_idx, end_token_idx) for matches
        """
        pass
