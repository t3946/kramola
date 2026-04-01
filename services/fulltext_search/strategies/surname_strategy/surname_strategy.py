from typing import Callable, List, Optional, Tuple, Union

from services.fulltext_search.check_id_collection import CheckIdCollection
from services.fulltext_search.phrase import Phrase
from services.fulltext_search.search_match import FTSMatch, FTSTextMatch
from services.fulltext_search.strategies.base_strategy import BaseSearchStrategy
from services.utils import normalize_text
from services.fulltext_search.strategies.surname_strategy.surname import Surname
from services.tokenization import Token, TokenDictionary


class SurnameStrategy(BaseSearchStrategy):
    @staticmethod
    def _norm_surname(value: str) -> str:
        return value.strip().casefold() if value else ""

    def search_all_phrases(
            self,
            source_tokens: list[Token],
            search_phrases: List[Tuple[Phrase, List[Token]]],
            dictionary: Optional[TokenDictionary] = None,
            on_source_token_proceed: Optional[Callable[[int, int], None]] = None,
            **kwargs: object,
    ) -> List[Tuple[Union[Phrase, str], List[FTSMatch]]]:
        # [start] progress
        progress_max_steps = len(source_tokens) + len(search_phrases)
        progress_step = 0

        def _continue_progress():
            nonlocal progress_step, progress_max_steps

            if on_source_token_proceed is not None:
                progress_step += 1
                on_source_token_proceed(progress_step, progress_max_steps)
        # [end]

        # [start] build token index
        source_tokens_index: dict[str, list[tuple[int, Token]]] = {}

        for i, token in enumerate(source_tokens):
            token_text_norm: str = normalize_text(token.text)
            prefix_len = min(len(token_text_norm), 3)
            key: str = token_text_norm[:prefix_len]

            if key not in source_tokens_index:
                source_tokens_index[key] = []

            source_tokens_index[key].append((i, token))
            _continue_progress()
        # [end]

        # [start] search
        check_id_collection: CheckIdCollection = CheckIdCollection()
        matches = []

        for phrase, _ in search_phrases:
            token_text_norm: str = normalize_text(phrase.phrase)
            prefix_len = min(len(token_text_norm), 3)
            key: str = token_text_norm[:prefix_len]
            surname = Surname(phrase.phrase)

            if key not in source_tokens_index:
                continue

            source_tokens_candidates: list[tuple[int, Token]] = source_tokens_index[key]

            for item in source_tokens_candidates:
                i, token = item

                if surname.check(token.text):
                    match = FTSTextMatch(
                        tokens=[source_tokens[i]],
                        start_token_idx=i,
                        end_token_idx=i,
                        search_phrase=phrase,
                        check_id=check_id_collection[(i, i)],
                    )

                    matches.append((phrase, [match]))

            _continue_progress()
        # [end]

        return matches
