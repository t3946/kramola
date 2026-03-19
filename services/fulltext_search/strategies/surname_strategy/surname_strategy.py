import uuid
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Union

from services.fulltext_search.check_id_collection import CheckIdCollection
from services.fulltext_search.phrase import Phrase
from services.fulltext_search.search_match import FTSMatch, FTSTextMatch
from services.fulltext_search.strategies.base_strategy import BaseSearchStrategy
from services.tokenization import Token, TokenDictionary


class SurnameStrategy(BaseSearchStrategy):
    @staticmethod
    def _norm_surname(value: str) -> str:
        return value.strip().casefold() if value else ""

    def _alphabetically_sort_surnames(self, surnames: list[str]) -> list[str]:
        return sorted(surnames, key=self._norm_surname)

    def _search_candidate_surnames(
        self,
        source_norm: str,
        sorted_norm_surnames: list[str],
    ) -> list[str]:
        prefix_len = min(len(source_norm), 3)
        source_prefix: str = source_norm[:prefix_len]
        result: list[str] = []

        for norm_surname in sorted_norm_surnames:
            search_prefix: str = norm_surname[:prefix_len]

            if source_prefix == search_prefix:
                result.append(norm_surname)

            if source_prefix < search_prefix:
                break

        return result

    def search_token_sequences(
        self,
        source_tokens: list[Token],
        search_tokens: list[Token],
        dictionary: Optional[TokenDictionary] = None,
    ) -> List[Tuple[int, int]]:
        if not search_tokens:
            return []

        search_norm: str = self._norm_surname(search_tokens[0].text)
        if not search_norm:
            return []

        prefix_len = min(len(search_norm), 3)
        search_prefix: str = search_norm[:prefix_len]
        matches: List[Tuple[int, int]] = []

        for idx, token in enumerate(source_tokens):
            source_norm: str = self._norm_surname(token.text)
            if source_norm[:prefix_len] == search_prefix:
                matches.append((idx, idx))

        return matches

    def search_all_phrases(
        self,
        source_tokens: list[Token],
        search_phrases: List[Tuple[Phrase, List[Token]]],
        dictionary: Optional[TokenDictionary] = None,
        **kwargs: object,
    ) -> List[Tuple[Union[Phrase, str], List[FTSMatch]]]:
        if not source_tokens or not search_phrases:
            return []

        norm_to_phrases: Dict[str, List[Phrase]] = defaultdict(list)

        for phrase, _ in search_phrases:
            norm_to_phrases[self._norm_surname(phrase.phrase)].append(phrase)

        sorted_norm_surnames: list[str] = self._alphabetically_sort_surnames(
            list(norm_to_phrases.keys())
        )
        phrase_matches: Dict[int, List[int]] = defaultdict(list)
        check_id_collection: CheckIdCollection = CheckIdCollection()

        for idx, token in enumerate(source_tokens):
            token_norm: str = self._norm_surname(token.text)
            if not token_norm:
                continue

            candidates: list[str] = self._search_candidate_surnames(
                token_norm,
                sorted_norm_surnames,
            )

            for norm_candidate in candidates:
                for phrase in norm_to_phrases[norm_candidate]:
                    phrase_matches[id(phrase)].append(idx)

        result_matches: List[Tuple[Union[Phrase, str], List[FTSMatch]]] = []

        for phrase, _ in search_phrases:
            indices: List[int] = phrase_matches.get(id(phrase), [])
            matches: List[FTSTextMatch] = [
                FTSTextMatch(
                    tokens=[source_tokens[i]],
                    start_token_idx=i,
                    end_token_idx=i,
                    search_phrase=phrase,
                    check_id=check_id_collection[(i, i)],
                )
                for i in indices
            ]
            result_matches.append((phrase, matches))

        return result_matches
