import bisect
from typing import Callable

from base_strategy import BaseSearchStrategy


class SurnameStrategy(BaseSearchStrategy):
    @staticmethod
    def _norm_surname(value: str) -> str:
        return value.strip().casefold() if value else ""

    def _alphabetically_sort_surnames(self, surnames: list[str]) -> list[str]:
        return sorted(surnames, key=self._norm_surname)

    def _search_candidate_surnames(
        self,
        source: str,
        search_surnames: list[str],
    ) -> list[str]:
        source_norm: str = self._norm_surname(source)
        prefix_len = min(len(source_norm), 3)
        source_prefix: str = source_norm[:prefix_len]
        result = []

        for surname in search_surnames:
            search_prefix = surname[:prefix_len]

            if source_prefix == search_prefix:
                result.append(surname)

            if source_prefix < search_prefix:
                break

        return result

    def search_all_phrases(
        self,
        source_tokens: list[str],
        search_surnames: list[str],
    ) -> list[str]:
        sorted_surnames: list[str] = self._alphabetically_sort_surnames(search_surnames)
        found_surnames: list[str] = []

        for token in source_tokens:
            candidates: list[str] = self._search_candidate_surnames(
                token,
                sorted_surnames,
            )

            for _ in candidates:
                pass

        return found_surnames

