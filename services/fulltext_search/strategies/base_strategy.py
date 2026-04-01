import uuid
from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional, Tuple, Union

from services.fulltext_search.phrase import Phrase
from services.fulltext_search.search_match import FTSMatch
from services.utils.regex_pattern import RegexPattern
from services.fulltext_search.search_match import FTSRegexMatch

from services.tokenization import Token, TokenDictionary


class BaseSearchStrategy(ABC):
    """Base class for search strategies."""

    @abstractmethod
    def search_all_phrases(
        self,
        source_tokens: List[Token],
        search_phrases: List[Tuple[Phrase, List[Token]]],
        dictionary: Optional[TokenDictionary] = None,
        regex_patterns: Optional[Dict[str, RegexPattern]] = None,
        on_source_token_proceed: Optional[Callable[[int, int], None]] = None,
    ) -> List[Tuple[Union[Phrase, str], List[FTSMatch]]]:
        """Search all phrases and return grouped matches."""

    def search_regex_matches(
        self,
        source_tokens: 'List[Token]',
        regex_patterns: Optional[Dict[str, RegexPattern]] = None,
        greedy: bool = False,
    ) -> List[FTSRegexMatch]:
        """
        Search regex pattern matches in concatenated text.
        
        This is effective for patterns that can span across multiple tokens
        (e.g., bypass patterns with special characters between letters).
        
        This method can be used to get information about regex-based matches
        separately from token-based matches.
        
        Args:
            source_tokens: Tokens from source text
            regex_patterns: Optional dictionary of {pattern_name: RegexPattern} for regex-based search
            
        Returns:
            List of FTSRegexMatch objects with token indices and pattern info
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

        concatenated_text_lower: str = concatenated_text.lower()
        matches: List[FTSRegexMatch] = []

        # Search all patterns in concatenated text
        for pattern_name, regex_pattern in regex_patterns.items():
            compiled_pattern = regex_pattern.compiled

            for match in compiled_pattern.finditer(concatenated_text_lower):
                match_start = match.start()
                match_end = match.end()

                # Find tokens that cover this match
                start_token_idx = self._find_token_by_position(token_positions, match_start)
                end_token_idx = self._find_token_by_position(token_positions, match_end - 1)

                if start_token_idx is not None and end_token_idx is not None:
                    matches.append(FTSRegexMatch(
                        tokens=source_tokens[start_token_idx:end_token_idx + 1],
                        start_token_idx=start_token_idx,
                        end_token_idx=end_token_idx,
                        regex_info=regex_pattern,
                        check_id = uuid.uuid1(),
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
