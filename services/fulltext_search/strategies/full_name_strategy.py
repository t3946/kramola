from typing import Callable, Dict, List, Optional, Tuple, Union

from services.declension_name import Declension
from services.fulltext_search.check_id_collection import CheckIdCollection
from services.fulltext_search.phrase import Phrase
from services.fulltext_search.search_match import FTSMatch, FTSTextMatch
from services.fulltext_search.strategies.base_strategy import BaseSearchStrategy
from services.tokenization import Token, TokenDictionary, TokenType
from services.utils import normalize_text
from services.utils.regex_pattern import RegexPattern


class FullNameStrategy(BaseSearchStrategy):
    @staticmethod
    def _norm_surname(value: str) -> str:
        return value.strip().casefold() if value else ""

    def _read_full_name(self, i: int, source_tokens: list[Token]) -> Optional[tuple[str, int, int]]:
        words = []
        j = i

        for token in source_tokens[i:]:
            if token.type == TokenType.WORD:
                words.append(normalize_text(token.text))

            if len(words) == 3:
                return ' '.join(words), i, j

            j += 1

        return None

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
        declension_service = Declension()

        for phrase, _ in search_phrases:
            token_text_norm: str = normalize_text(phrase.phrase)
            prefix_len = min(len(token_text_norm), 3)
            key: str = token_text_norm[:prefix_len]

            if key not in source_tokens_index:
                continue

            source_tokens_candidates: list[tuple[int, Token]] = source_tokens_index[key]
            search_names = declension_service.decline_full_name(token_text_norm)

            for item in source_tokens_candidates:
                i, token = item
                full_name_data: Optional[tuple[str, int, int]] = self._read_full_name(i, source_tokens)

                if full_name_data is None:
                    continue

                source_name, i, j = full_name_data

                if source_name in search_names:
                    match = FTSTextMatch(
                        tokens=source_tokens[i:j],
                        start_token_idx=i,
                        end_token_idx=j,
                        search_phrase=phrase,
                        check_id=check_id_collection[(i, j)],
                    )

                    matches.append((phrase, [match]))

            _continue_progress()
        # [end]

        return matches
