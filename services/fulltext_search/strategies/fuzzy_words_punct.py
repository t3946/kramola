from typing import List, Tuple, TYPE_CHECKING, Optional
from services.fulltext_search.strategies.base_strategy import BaseSearchStrategy
from services.fulltext_search.dictionary import TokenDictionary

if TYPE_CHECKING:
    from services.fulltext_search.fulltext_search import Token


class FuzzyWordsPunctStrategy(BaseSearchStrategy):
    """
    Search strategy with strict word order but fuzzy punctuation.
    
    Words must match in strict order by lemma/stem, but punctuation is ignored.
    """

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
        source_len = len(source_tokens)
        search_len = len(search_tokens)

        if search_len == 0:
            return []

        search_words_count = sum(1 for t in search_tokens if t['type'] == 'word')

        if search_words_count == 0:
            return []

        if dictionary is not None and len(search_tokens) > 0:
            search_words = [t for t in search_tokens if t['type'] == 'word']

            if len(search_words) > 0:
                first_word = search_words[0]
                candidate_starts = dictionary.find_candidate_positions(first_word)

                for start_idx in candidate_starts:
                    source_i = start_idx
                    search_j = 0
                    match_start = None
                    words_matched = 0

                    while source_i < source_len and search_j < search_len:
                        source_token = source_tokens[source_i]
                        search_token = search_tokens[search_j]

                        if source_token['type'] in ('punct', 'space'):
                            source_i += 1
                            continue

                        if search_token['type'] in ('punct', 'space'):
                            search_j += 1
                            continue

                        if match_start is None:
                            match_start = source_i

                        if source_token['type'] == 'word' and search_token['type'] == 'word':
                            match_by_text = source_token['text'] == search_token['text']
                            match_by_lemma = source_token['lemma'] == search_token['lemma']
                            match_by_stem = source_token['stem'] == search_token['stem']

                            if match_by_text or match_by_lemma and match_by_stem:
                                source_i += 1
                                search_j += 1
                                words_matched += 1
                            else:
                                break
                        else:
                            break

                    if words_matched == search_words_count:
                        matches.append((match_start, source_i - 1))

                return matches

        i = 0

        while i < source_len:
            source_i = i
            search_j = 0
            match_start = None
            words_matched = 0

            while source_i < source_len and search_j < search_len:
                source_token = source_tokens[source_i]
                search_token = search_tokens[search_j]

                if source_token['type'] in ('punct', 'space'):
                    source_i += 1
                    continue

                if search_token['type'] in ('punct', 'space'):
                    search_j += 1
                    continue

                if match_start is None:
                    match_start = source_i

                if source_token['type'] == 'word' and search_token['type'] == 'word':
                    match_by_text = source_token['text'] == search_token['text']
                    match_by_lemma = source_token['lemma'] == search_token['lemma']
                    match_by_stem = source_token['stem'] == search_token['stem']

                    if match_by_text or match_by_lemma or match_by_stem:
                        source_i += 1
                        search_j += 1
                        words_matched += 1
                    else:
                        break
                else:
                    break

            if words_matched == search_words_count:
                matches.append((match_start, source_i - 1))
                i = source_i
            else:
                i += 1

        return matches

    def _verify_phrase_match(
        self,
        source_tokens: 'List[Token]',
        search_words: 'List[Token]',
        start_token_idx: int
    ) -> Optional[Tuple[int, int]]:
        """
        Verify if phrase matches starting from start_token_idx.
        
        Args:
            source_tokens: Source tokens
            search_words: Search words (only words, no punctuation)
            start_token_idx: Starting token index
            
        Returns:
            (start, end) tuple if match found, None otherwise
        """
        source_i = start_token_idx
        search_j = 0
        match_start = None
        words_matched = 0
        source_len = len(source_tokens)

        while source_i < source_len and search_j < len(search_words):
            source_token = source_tokens[source_i]

            if source_token['type'] in ('punct', 'space'):
                source_i += 1
                continue

            search_token = search_words[search_j]

            if match_start is None:
                match_start = source_i

            if source_token['type'] == 'word':
                source_text = source_token['text']
                source_lemma = source_token['lemma']
                source_stem = source_token['stem']
                search_text = search_token['text']
                search_lemma = search_token['lemma']
                search_stem = search_token['stem']

                if (source_text == search_text or
                    source_lemma == search_lemma or
                    source_stem == search_stem):
                    source_i += 1
                    search_j += 1
                    words_matched += 1
                else:
                    return None
            else:
                return None

        if words_matched == len(search_words):
            return (match_start, source_i - 1)
        return None

    def search_all_phrases(
        self,
        source_tokens: 'List[Token]',
        search_phrases: List[Tuple[str, 'List[Token]']],
        dictionary: Optional[TokenDictionary] = None
    ) -> List[Tuple[str, List[Tuple[int, int]]]]:
        """
        Search all phrases in one pass using dictionary optimization.
        
        Args:
            source_tokens: Source tokens
            search_phrases: List of (phrase_text, tokens) tuples
            dictionary: Optional dictionary for faster lookup
            
        Returns:
            List of (phrase_text, matches) tuples where matches is list of (start, end) tuples
        """
        if not source_tokens or not search_phrases:
            return []

        if dictionary is None:
            dictionary = TokenDictionary(source_tokens)

        results = []

        for phrase_text, search_tokens in search_phrases:
            search_words = [t for t in search_tokens if t['type'] == 'word']

            if len(search_words) == 0:
                results.append((phrase_text, []))
                continue

            first_word = search_words[0]
            candidate_starts = dictionary.find_candidate_positions(first_word)
            matches = []

            for start_idx in candidate_starts:
                match_result = self._verify_phrase_match(source_tokens, search_words, start_idx)

                if match_result:
                    matches.append(match_result)

            results.append((phrase_text, matches))

        return results
