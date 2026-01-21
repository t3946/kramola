import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Tuple, TYPE_CHECKING, Optional, Dict
from services.utils.regex_pattern import RegexPattern

if TYPE_CHECKING:
    from services.fulltext_search.token import Token
    from services.fulltext_search.dictionary import TokenDictionary
else:
    from services.fulltext_search.token import Token


@dataclass
class RegexMatch:
    """Information about a regex pattern match."""
    start_token_idx: int
    end_token_idx: int
    pattern: RegexPattern
    matched_text: str


class BaseSearchStrategy(ABC):
    """Base class for search strategies."""

    def search_regex_matches(
        self,
        source_tokens: 'List[Token]',
        regex_patterns: Optional[Dict[str, str]] = None
    ) -> List[RegexMatch]:
        """
        Search regex pattern matches in concatenated text.
        
        This is effective for patterns that can span across multiple tokens
        (e.g., bypass patterns with special characters between letters).
        
        This method can be used to get information about regex-based matches
        separately from token-based matches.
        
        Args:
            source_tokens: Tokens from source text
            regex_patterns: Optional dictionary of {pattern_name: pattern_string} for regex-based search
            
        Returns:
            List of RegexMatch objects with token indices and pattern info
        """
        if not source_tokens or not regex_patterns:
            return []

        # Build concatenated text and token position mapping
        concatenated_text = ''
        token_positions: List[Tuple[int, int]] = []

        for token in source_tokens:
            start_pos = len(concatenated_text)
            concatenated_text += token.text
            end_pos = len(concatenated_text)
            token_positions.append((start_pos, end_pos))

        concatenated_text_lower = concatenated_text.lower()
        matches: List[RegexMatch] = []

        # Search all patterns in concatenated text
        for pattern_name, pattern_str in regex_patterns.items():
            regex_pattern = RegexPattern(pattern_name=pattern_name, pattern=pattern_str)
            compiled_pattern = regex_pattern.compiled

            for match in compiled_pattern.finditer(concatenated_text_lower):
                match_start = match.start()
                match_end = match.end()
                matched_text = match.group(0)

                # Find tokens that cover this match
                start_token_idx = self._find_token_by_position(token_positions, match_start)
                end_token_idx = self._find_token_by_position(token_positions, match_end - 1)

                if start_token_idx is not None and end_token_idx is not None:
                    matches.append(RegexMatch(
                        start_token_idx=start_token_idx,
                        end_token_idx=end_token_idx,
                        pattern=regex_pattern,
                        matched_text=matched_text
                    ))

        return matches

    @staticmethod
    def _find_token_by_position(
        token_positions: List[Tuple[int, int]],
        position: int
    ) -> Optional[int]:
        """Find token index that contains given position in concatenated text."""
        for idx, (start_pos, end_pos) in enumerate(token_positions):
            if start_pos <= position < end_pos:
                return idx
        return None

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
