from typing import List, Tuple, TYPE_CHECKING, Optional
from services.fulltext_search.strategies.base_strategy import BaseSearchStrategy
from services.fulltext_search.dictionary import TokenDictionary
from commands.test_word2vec import CheckSwearWord

if TYPE_CHECKING:
    from services.fulltext_search.token import Token, TokenType
    from services.fulltext_search.dictionary import TokenDictionary
else:
    from services.fulltext_search.token import Token, TokenType


class SwearWordsStrategy(BaseSearchStrategy):
    """
    Search strategy that uses lemmas, stems, and regex patterns for swear words.
    
    Words can match by lemma/stem (as in other strategies) or by regex patterns
    from CheckSwearWord class.
    
    Note: This strategy is designed for single words only. Swear words are always
    single words, so phrase search is not needed.
    """

    def __init__(self) -> None:
        self.swear_checker: CheckSwearWord = CheckSwearWord()

    def _match_tokens(
        self,
        source_token: 'Token',
        search_token: 'Token'
    ) -> bool:
        """
        Check if two tokens match.
        
        First priority: lemma/stem match
        Second priority: regex pattern match via CheckSwearWord
        """
        # Tokens must have the same type
        if source_token.type != search_token.type:
            return False

        # For non-word tokens (punctuation, spaces), check exact text match
        if source_token.type != TokenType.WORD:
            return source_token.text == search_token.text

        # [start] First priority: check lemma/stem match
        match_by_text = source_token.text == search_token.text
        match_by_lemma = source_token.lemma == search_token.lemma
        match_by_stem = source_token.stem == search_token.stem

        if match_by_text or match_by_lemma or match_by_stem:
            return True
        # [end]

        # [start] Second priority: check regex patterns via CheckSwearWord
        # If lemma/stem didn't match, try to match by swear word patterns
        source_text = source_token.text.lower()
        search_text = search_token.text.lower()

        match_by_swear_source = self.swear_checker.check(source_text)
        match_by_swear_search = self.swear_checker.check(search_text)

        # Match if at least one word passes the swear word check
        if match_by_swear_source or match_by_swear_search:
            return True
        # [end]

        return False

    def search_token_sequences(
        self,
        source_tokens: 'List[Token]',
        search_tokens: 'List[Token]',
        dictionary: Optional['TokenDictionary'] = None
    ) -> List[Tuple[int, int]]:
        """
        Search single word only (swear words are always single words).
        
        Returns (start, end) where start and end are source tokens indices.
        """
        matches: List[Tuple[int, int]] = []

        # Extract only word tokens from search (ignore punctuation and spaces)
        search_words = [t for t in search_tokens if t.type == TokenType.WORD]

        # This strategy works only for single words
        if len(search_words) != 1:
            return []

        search_word = search_words[0]

        # [start] Optimized search using dictionary
        if dictionary is not None:
            candidate_starts = dictionary.find_candidate_positions(search_word)

            for start_idx in candidate_starts:
                if start_idx < len(source_tokens):
                    source_token = source_tokens[start_idx]

                    if source_token.type == TokenType.WORD:
                        if self._match_tokens(source_token, search_word):
                            matches.append((start_idx, start_idx))

            return matches
        # [end]

        # [start] Fallback: linear search without dictionary
        for i, source_token in enumerate(source_tokens):
            if source_token.type == TokenType.WORD:
                if self._match_tokens(source_token, search_word):
                    matches.append((i, i))
        # [end]

        # [start] Special feature: search in concatenated text for bypass patterns
        # This is effective for bypass patterns that can span across multiple tokens
        concatenated_matches = self._search_in_concatenated_text(source_tokens)
        matches.extend(concatenated_matches)
        # [end]

        return matches

    def _search_in_concatenated_text(
        self,
        source_tokens: 'List[Token]'
    ) -> List[Tuple[int, int]]:
        """
        Search swear words in concatenated text (effective for bypass patterns).
        
        Concatenates all tokens, searches for patterns, then maps matches back to tokens.
        """
        if not source_tokens:
            return []

        # Build concatenated text and token position mapping
        concatenated_text = ''
        token_positions: List[Tuple[int, int]] = []  # (start_pos, end_pos) for each token

        for token in source_tokens:
            start_pos = len(concatenated_text)
            concatenated_text += token.text
            end_pos = len(concatenated_text)
            token_positions.append((start_pos, end_pos))

        concatenated_text_lower = concatenated_text.lower()
        matches: List[Tuple[int, int]] = []

        # Search all compiled patterns in concatenated text
        compiled_patterns = CheckSwearWord._get_compiled_patterns()

        for pattern in compiled_patterns.values():
            for match in pattern.finditer(concatenated_text_lower):
                match_start = match.start()
                match_end = match.end()

                # Find tokens that cover this match
                start_token_idx = self._find_token_by_position(token_positions, match_start)
                end_token_idx = self._find_token_by_position(token_positions, match_end - 1)

                if start_token_idx is not None and end_token_idx is not None:
                    matches.append((start_token_idx, end_token_idx))

        return matches

    def _find_token_by_position(
        self,
        token_positions: List[Tuple[int, int]],
        position: int
    ) -> Optional[int]:
        """
        Find token index that contains given position in concatenated text.
        """
        for idx, (start_pos, end_pos) in enumerate(token_positions):
            if start_pos <= position < end_pos:
                return idx
        return None
