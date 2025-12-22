from typing import List, Tuple, TYPE_CHECKING
from services.analyser.strategies.base_strategy import BaseSearchStrategy

if TYPE_CHECKING:
    from services.analyser.fulltext_search import Token


class StrictOrderFuzzyPunctStrategy(BaseSearchStrategy):
    """
    Search strategy with strict word order but fuzzy punctuation.
    
    Words must match in strict order by lemma/stem, but punctuation is ignored.
    """

    def search_token_sequences(
        self,
        source_tokens: 'List[Token]',
        search_tokens: 'List[Token]'
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
