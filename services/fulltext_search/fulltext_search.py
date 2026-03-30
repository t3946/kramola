from enum import Enum
from typing import List, Optional, Tuple, Union, Dict

from services.fulltext_search.phrase import EType, Phrase
from services.progress.combined_progress.combined_progress import CombinedProgress
from services.pymorphy_service import CYRILLIC_PATTERN
from services.tokenization import Token, TokenDictionary
from services.tokenization.tokenizer import Tokenizer
from services.utils.regex_pattern import RegexPattern
from services.fulltext_search.search_match import FTSMatch
from services.fulltext_search.strategies import (
    FuzzyWordsPunctStrategy,
    SurnameStrategy,
)

USE_STEM_FALLBACK = True
STOP_WORDS_RU = {
    "и", "а", "но", "да", "или", "либо", "то", "не то", "тоже", "также",
    "зато", "однако", "же", "что", "чтобы", "как", "будто", "словно",
    "если", "когда", "пока", "едва", "лишь", "потому что", "так как",
    "ибо", "оттого что", "поскольку", "хотя", "хоть", "несмотря на то что",
    "пускай", "пусть", "словно", "точно", "чем", "так что", "поэтому", "причем", "притом",
    "в", "на", "с", "о", "у", "к", "по", "за", "из", "от", "до", "под",
    "над", "при", "без", "для", "про", "об", "обо", "со", "ко", "из-за",
    "из-под", "через", "перед", "между", "среди", "возле", "около",
    "вокруг", "вдоль", "вместо", "внутри", "вне", "кроме", "помимо",
    "сверх", "сквозь", "согласно", "благодаря", "вопреки", "навстречу",
    "ввиду", "вследствие", "наподобие", "насчет", "спустя",
    "не", "бы", "ли", "её",
    "а", "б", "в", "г", "д", "е", "ё", "ж", "з", "и", "й", "к", "л", "м",
    "н", "о", "п", "р", "с", "т", "у", "ф", "х", "ц", "ч", "ш", "щ", "ъ",
    "ы", "ь", "э", "ю", "я"
}
STOP_WORDS_EN = {
    "and", "but", "or", "nor", "for", "so", "yet",
    "after", "although", "as", "because", "before", "if", "once",
    "since", "than", "that", "though", "till", "unless", "until",
    "when", "whenever", "where", "whereas", "wherever", "whether", "while",
    "a", "an", "the", "this", "that", "these", "those",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them",
    "my", "your", "his", "her", "its", "our", "their",
    "am", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having", "do", "does", "did", "doing",
    "will", "would", "should", "could", "may", "might", "must", "can"
}


class SearchStrategy(Enum):
    """Search strategy enum."""
    FUZZY_WORDS_PUNCT = "fuzzy_words_punct"
    SURNAME = "surname"


class FulltextSearch:
    """
    Implements fulltext search algorithms.

    Provides methods for text tokenization and matching
    by words and phrases using lemmatization and stemming.
    """

    _default_strategy = FuzzyWordsPunctStrategy()
    _progress: Optional[CombinedProgress] = None
    PARTICLE_KEY = 'fulltext_search'

    def __init__(
        self,
        source: Union[str, List[Token]],
        combined_progress: Optional[CombinedProgress] = None,
    ):
        """
        Initialize FulltextSearch with source text or tokens.

        Args:
            source: Source text (str) or list of tokens to search in
            combined_progress: When source is str, passed to Tokenizer for particle progress
        """
        self._tokenizer: Tokenizer = Tokenizer(combined_progress)
        self._progress: Optional[CombinedProgress] = combined_progress

        if isinstance(source, str):
            self.source_tokens: List[Token] = self._tokenizer.tokenize_text(source)
        else:
            self.source_tokens: List[Token] = source

        self.dictionary: TokenDictionary = TokenDictionary(self.source_tokens)

    @staticmethod
    def _get_strategy(strategy: Optional[SearchStrategy] = None):
        """Get strategy instance by enum value."""
        if strategy is None:
            return FulltextSearch._default_strategy

        if strategy == SearchStrategy.FUZZY_WORDS_PUNCT:
            return FuzzyWordsPunctStrategy()
        elif strategy == SearchStrategy.SURNAME:
            return SurnameStrategy()

        return FulltextSearch._default_strategy

    def search(
        self,
        text: Union[str, List[Token]],
        strategy: Optional[SearchStrategy] = None
    ) -> List[Tuple[int, int]]:
        """
        Search for text or tokens in source.
        
        Args:
            text: Search text (str) or list of tokens to search for
            strategy: Search strategy to use (default: FUZZY_WORDS_PUNCT)
            
        Returns:
            List of tuples (start, end) where start and end are source tokens indices.
        """
        if isinstance(text, str):
            search_tokens: List[Token] = self._tokenizer.tokenize_text(text)
        else:
            search_tokens: List[Token] = text

        strategy_instance = FulltextSearch._get_strategy(strategy)
        return strategy_instance.search_token_sequences(
            self.source_tokens,
            search_tokens,
            self.dictionary
        )

    def _update_progress_value(self, value: float) -> None:
        if self._progress is None:
            return

        self._progress.set_particle_value(
            key=FulltextSearch.PARTICLE_KEY,
            value=value,
        )

    def _update_progress_description(self, description: str) -> None:
        if self._progress is None:
            return

        self._progress.set_particle_description(
            FulltextSearch.PARTICLE_KEY,
            description,
        )

    def search_all(
        self,
        search_phrases: List[Tuple[Phrase, Union[str, List[Token]]]],
        search_patterns: Optional[Dict[str, RegexPattern]] = None,
        text_strategy: Optional[SearchStrategy] = None,
    ) -> List[Tuple[Union[Phrase, str], List[FTSMatch]]]:
        self._update_progress_value(0)
        """
        Search all phrases in one pass.

        Args:
            search_phrases: List of (phrase, text_or_tokens) tuples
            text_strategy: Search strategy for Phrases with type TEXT (default: FUZZY_WORDS_PUNCT)
            search_patterns: Optional dictionary of {pattern_name: RegexPattern} for regex-based search

        Returns:
            List of (phrase or str, matches) tuples where matches is list of FTSMatch objects
        """
        text_strategy_instance = FulltextSearch._get_strategy(text_strategy)
        surname_strategy_instance = FulltextSearch._get_strategy(SearchStrategy.SURNAME)

        text_phrases_tokens: List[Tuple[Phrase, List[Token]]] = []
        surname_phrases_tokens: List[Tuple[Phrase, List[Token]]] = []

        for phrase, text_or_tokens in search_phrases:
            search_tokens = (
                self._tokenizer.tokenize_text(text_or_tokens)
                if isinstance(text_or_tokens, str)
                else text_or_tokens
            )
            pair: Tuple[Phrase, List[Token]] = (phrase, search_tokens)

            if phrase.phrase_type == EType.TEXT:
                text_phrases_tokens.append(pair)
            elif phrase.phrase_type == EType.SURNAME:
                surname_phrases_tokens.append(pair)

        phrase_to_matches: Dict[Union[int, str], Tuple[Union[Phrase, str], List[FTSMatch]]] = {}

        def _add_matches(phrase: Union[Phrase, str], matches: List[FTSMatch]) -> None:
            if isinstance(phrase, Phrase):
                phrase_id = id(phrase)
            else:
                phrase_id = phrase

            if phrase_to_matches.get(phrase_id) is None:
                phrase_to_matches[phrase_id] = (phrase, [])

            _, prev_matches = phrase_to_matches[phrase_id]
            prev_matches.extend(matches)
            phrase_to_matches[phrase_id] = (phrase, prev_matches)

        def _on_source_token_proceed(proceed, total):
            if total == 0:
                self._update_progress_value(value=100)
                return

            threshold = max(round(total * 0.05), 1)

            if proceed % threshold != 0:
                return

            self._update_progress_value(value=proceed / total * 100)

        patterns: Dict[str, RegexPattern] = search_patterns if search_patterns is not None else {}

        # progress total
        text_search_all_phrases_total = len(text_phrases_tokens)
        surnames_search_all_phrases_total = len(self.source_tokens) + len(surname_phrases_tokens)
        progress_total = text_search_all_phrases_total + surnames_search_all_phrases_total

        if len(text_phrases_tokens) > 0 or len(patterns) > 0:
            regex_arg: Optional[Dict[str, RegexPattern]] = patterns if len(patterns) > 0 else None

            text_results: List[Tuple[Union[Phrase, str], List[FTSMatch]]] = (
                text_strategy_instance.search_all_phrases(
                    source_tokens=self.source_tokens,
                    search_phrases=text_phrases_tokens,
                    dictionary=self.dictionary,
                    regex_patterns=regex_arg,
                    on_source_token_proceed=lambda proceed, total: _on_source_token_proceed(proceed, progress_total),
                )
            )

            for phrase, matches in text_results:
                _add_matches(phrase, matches)

        if len(surname_phrases_tokens) > 0:
            surname_results: List[Tuple[Union[Phrase, str], List[FTSMatch]]] = (
                surname_strategy_instance.search_all_phrases(
                    source_tokens=self.source_tokens,
                    search_phrases=surname_phrases_tokens,
                    on_source_token_proceed=lambda proceed, total: _on_source_token_proceed(
                        len(text_phrases_tokens) + proceed,
                        progress_total
                    ),
                )
            )

            for phrase, matches in surname_results:
                _add_matches(phrase, matches)

        result: List[Tuple[Union[Phrase, str], List[FTSMatch]]] = []

        for phrase, _ in search_phrases:
            if phrase_to_matches.get(id(phrase)) is None:
                continue

            _, matches = phrase_to_matches.get(id(phrase))
            result.append((phrase, matches))

        # [start] convert regex matches to phrase matches
        for _, pattern in patterns.items():
            key = 'regex ' + pattern.pattern_name

            if phrase_to_matches.get(key) is None:
                continue

            _, matches = phrase_to_matches.get(key)
            phrase = Phrase(
                phrase=pattern.pattern_name,
                source_list=pattern.source_list,
                phrase_original=None,
                phrase_type=EType.TEXT,
                model=None,
            )

            result.append((phrase, matches))
        # [end]

        self._update_progress_value(100)
        return result

    @staticmethod
    def _is_stop_word(lemma: str) -> bool:
        """Checks if lemma is a stop word."""
        if not lemma:
            return False

        is_russian = bool(CYRILLIC_PATTERN.search(lemma))
        stop_words_set = STOP_WORDS_RU if is_russian else STOP_WORDS_EN

        return lemma in stop_words_set

    @staticmethod
    def _compare_token_sequences(
        source_tokens: List[Token],
        search_tokens: List[Token],
        strategy: Optional[SearchStrategy] = None
    ) -> bool:
        """
        Compares two token sequences of the same length.
        Match is considered according to selected strategy.
        Works only with FUZZY_WORDS_PUNCT token-by-token comparison helper.
        
        Args:
            source_tokens: Tokens from source text
            search_tokens: Tokens from search query
            strategy: Search strategy to use (default: FUZZY_WORDS_PUNCT)
            
        Returns:
            True if sequences match according to strategy, False otherwise
        """
        strategy_instance = FulltextSearch._get_strategy(strategy)

        if not isinstance(strategy_instance, FuzzyWordsPunctStrategy):
            raise ValueError("_compare_token_sequences is only available for FUZZY_WORDS_PUNCT strategy")

        return FuzzyWordsPunctStrategy._compare_token_sequences(source_tokens, search_tokens)

    @staticmethod
    def search_token_sequences(
        source_tokens: List[Token],
        search_tokens: List[Token],
        strategy: Optional[SearchStrategy] = None
    ) -> List[Tuple[int, int]]:
        """
        Search token sequences.
        
        Args:
            source_tokens: Tokens from source text
            search_tokens: Tokens from search query
            strategy: Search strategy to use (default: FUZZY_WORDS_PUNCT)
            
        Returns:
            List of tuples (start, end) where start and end are source tokens indices.
        """
        strategy_instance = FulltextSearch._get_strategy(strategy)
        dictionary = TokenDictionary(source_tokens)
        return strategy_instance.search_token_sequences(source_tokens, search_tokens, dictionary)
