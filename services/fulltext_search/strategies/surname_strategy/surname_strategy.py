import uuid
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Union

from services.fulltext_search.check_id_collection import CheckIdCollection
from services.fulltext_search.phrase import Phrase
from services.fulltext_search.search_match import FTSMatch, FTSTextMatch
from services.fulltext_search.strategies.base_strategy import BaseSearchStrategy
from services.fulltext_search.strategies.surname_strategy.surname import Surname
from services.tokenization import Token, TokenDictionary
from services.utils.timeit import timeit


class SurnameStrategy(BaseSearchStrategy):
    @staticmethod
    def _norm_surname(value: str) -> str:
        return value.strip().casefold() if value else ""

    def _alphabetically_sort_surnames(self, surnames: list[str]) -> list[str]:
        return sorted(surnames, key=self._norm_surname)

    def _search_candidate_surnames(
            self,
            source_norm: str,
            search_phrases: list[Phrase],
    ) -> list[Phrase]:
        prefix_len = min(len(source_norm), 3)
        source_prefix: str = source_norm[:prefix_len]
        result: list[Phrase] = []

        for phrase in search_phrases:
            search_prefix: str = self._norm_surname(phrase.phrase[:prefix_len])

            if source_prefix == search_prefix:
                result.append(phrase)

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
        check_id_collection: CheckIdCollection = CheckIdCollection()
        matches = []

        for i, token in enumerate(source_tokens):
            token_text_norm: str = self._norm_surname(token.text)
            phrases_filtered: list[Phrase] = self._search_candidate_surnames(
                source_norm=token_text_norm,
                search_phrases=[phrase for phrase, _ in search_phrases],
            )

            for phrase in phrases_filtered:
                surname: Surname = Surname(phrase.phrase)

                if surname.check(token_text_norm):
                    match = FTSTextMatch(
                        tokens=[source_tokens[i]],
                        start_token_idx=i,
                        end_token_idx=i,
                        search_phrase=phrase,
                        check_id=check_id_collection[(i, i)],
                    )

                    # todo: здесь возможно неверно заполняется итоговый matches
                    matches.append((phrase, [match]))

        return matches
