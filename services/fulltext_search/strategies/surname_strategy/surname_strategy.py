from typing import Callable, Dict, List, Optional, Tuple, Union

from services.fulltext_search.check_id_collection import CheckIdCollection
from services.fulltext_search.phrase import Phrase
from services.fulltext_search.search_match import FTSMatch, FTSTextMatch
from services.fulltext_search.strategies.base_strategy import BaseSearchStrategy
from services.fulltext_search.strategies.surname_strategy.surname import Surname
from services.tokenization import Token, TokenDictionary, TokenType
from services.utils import normalize_text
from services.utils.regex_pattern import RegexPattern


class SurnameStrategy(BaseSearchStrategy):
    @staticmethod
    def _norm_surname(value: str) -> str:
        return value.strip().casefold() if value else ""

    def search_all_phrases(
        self,
        source_tokens: list[Token],
        search_phrases: List[Tuple[Phrase, List[Token]]],
        dictionary: Optional[TokenDictionary] = None,
        regex_patterns: Optional[Dict[str, RegexPattern]] = None,
        on_source_token_proceed: Optional[Callable[[int, int], None]] = None,
    ) -> List[Tuple[Union[Phrase, str], List[FTSMatch]]]:
        _ = dictionary
        _ = regex_patterns

        # [start] progress
        progress_max_steps = len(source_tokens) + len(search_phrases)
        progress_step = 0

        def _continue_progress(step = 1):
            nonlocal progress_step, progress_max_steps

            if on_source_token_proceed is not None:
                progress_step += step
                on_source_token_proceed(progress_step, progress_max_steps)

        # [end]

        # [start] build token index
        source_tokens_index: dict[str, list[tuple[int, int, list[Token]]]] = {}
        i = 0

        while i < len(source_tokens):
            token = source_tokens[i]

            if token.type != TokenType.WORD:
                i += 1
                continue

            # [start] double surname: "Кара-Мурза"
            next_token_1: Optional[Token] = source_tokens[i + 1] if i + 1 < len(source_tokens) else None
            next_token_2: Optional[Token] = source_tokens[i + 2] if i + 2 < len(source_tokens) else None
            double_surname = next_token_1 and next_token_2 and next_token_1.text == '-' and next_token_2.type == TokenType.WORD
            # [end]

            if double_surname:
                token_text_norm: str = normalize_text(''.join([token.text, next_token_1.text, next_token_2.text]))
                prefix_len = min(len(token_text_norm), 3)
                key: str = token_text_norm[:prefix_len]

                if key not in source_tokens_index:
                    source_tokens_index[key] = []

                source_tokens_index[key].append((i, i + 3, [token, next_token_1, next_token_2]))
                _continue_progress(3)
                i += 3
            else:
                token_text_norm: str = normalize_text(token.text)
                prefix_len = min(len(token_text_norm), 3)
                key: str = token_text_norm[:prefix_len]

                if key not in source_tokens_index:
                    source_tokens_index[key] = []

                source_tokens_index[key].append((i, i, [token]))
                _continue_progress()
                i += 1
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

            source_tokens_candidates: list[tuple[int, int, list[Token]]] = source_tokens_index[key]

            for item in source_tokens_candidates:
                i, j, tokens = item
                tokens_text: str = ''.join([token.text for token in tokens])

                if surname.check(tokens_text):
                    match = FTSTextMatch(
                        tokens=tokens,
                        start_token_idx=i,
                        end_token_idx=j,
                        search_phrase=phrase,
                        check_id=check_id_collection[(i, j)],
                    )

                    matches.append((phrase, [match]))

            _continue_progress()
        # [end]

        return matches
