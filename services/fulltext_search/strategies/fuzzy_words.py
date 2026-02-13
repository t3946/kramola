from typing import List, Tuple, Optional, Dict
from services.fulltext_search.strategies.base_strategy import BaseSearchStrategy

from services.tokenization import Token, TokenType, TokenDictionary


class FuzzyWordsStrategy(BaseSearchStrategy):
    """
    Search strategy with fuzzy word matching but strict order and punctuation.
    
    Words can match by lemma/stem, but token types and order must be exact.
    """

    @staticmethod
    def _compare_token_sequences(
        source_tokens: 'List[Token]',
        search_tokens: 'List[Token]'
    ) -> bool:
        """
        Compares two token sequences of the same length.
        Match is considered if lemmas or stems match.
        Token types must match exactly.
        """
        if len(source_tokens) != len(search_tokens):
            return False

        for t1, t2 in zip(source_tokens, search_tokens):
            if t1.type != t2.type:
                return False

            match_by_text = t1.text == t2.text
            match_by_lemma = False
            match_by_stem = False

            if t1.type == TokenType.WORD:
                match_by_lemma = t1.lemma == t2.lemma
                match_by_stem = t1.stem == t2.stem

            match = match_by_text or match_by_lemma or match_by_stem

            if not match:
                return False

        return True

    def search_token_sequences(
        self,
        source_tokens: 'List[Token]',
        search_tokens: 'List[Token]',
        dictionary: Optional['TokenDictionary'] = None
    ) -> List[Tuple[int, int]]:
        """
        Search token sequences.
        Returns (start, end) where start and end are source tokens indices.
        """
        matches = []
        search_len = len(search_tokens)

        if search_len == 0:
            return []

        source_len = len(source_tokens)

        if dictionary is not None and len(search_tokens) > 0:
            first_token = search_tokens[0]
            candidate_starts = dictionary.find_candidate_positions(first_token)

            for i in sorted(candidate_starts):
                if i + search_len - 1 >= source_len:
                    continue

                sub_sequence = source_tokens[i:i+search_len]
                match_found = self._compare_token_sequences(sub_sequence, search_tokens)

                if match_found:
                    matches.append((i, i + search_len - 1))

            return matches

        i = 0

        while i + search_len - 1 < len(source_tokens):
            sub_sequence = source_tokens[i:i+search_len]
            match_found = self._compare_token_sequences(sub_sequence, search_tokens)

            if match_found:
                matches.append((i, i + search_len - 1))
                i += search_len
            else:
                i += 1

        return matches
