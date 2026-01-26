import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple, Union, Dict
from services.pymorphy_service import CYRILLIC_PATTERN, ensure_models_loaded
from services import pymorphy_service
from services.utils.regex_pattern import RegexPattern
from services.fulltext_search.search_match import FTSMatch, FTSTextMatch, FTSRegexMatch
from services.fulltext_search.strategies import (
    FuzzyWordsStrategy,
    FuzzyWordsPunctStrategy
)
from services.fulltext_search.dictionary import TokenDictionary
from services.fulltext_search.token import Token, TokenType

TOKENIZE_PATTERN_UNIVERSAL = re.compile(r"(\w+)|([^\w\s]+)|(\s+)", re.UNICODE)
PYMORPHY_AVAILABLE = True

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
    FUZZY_WORDS = "fuzzy_words"
    FUZZY_WORDS_PUNCT = "fuzzy_words_punct"


class FulltextSearch:
    """
    Implements fulltext search algorithms.

    Provides methods for text tokenization and matching
    by words and phrases using lemmatization and stemming.
    """

    _default_strategy = FuzzyWordsStrategy()

    def __init__(self, source: Union[str, List[Token]]):
        """
        Initialize FulltextSearch with source text or tokens.
        
        Args:
            source: Source text (str) or list of tokens to search in
        """
        if isinstance(source, str):
            self.source_tokens: List[Token] = FulltextSearch.tokenize_text(source)
        else:
            self.source_tokens: List[Token] = source

        self.dictionary: TokenDictionary = TokenDictionary(self.source_tokens)

    @staticmethod
    def _get_strategy(strategy: Optional[SearchStrategy] = None):
        """Get strategy instance by enum value."""
        if strategy is None:
            return FulltextSearch._default_strategy

        if strategy == SearchStrategy.FUZZY_WORDS:
            return FuzzyWordsStrategy()
        elif strategy == SearchStrategy.FUZZY_WORDS_PUNCT:
            return FuzzyWordsPunctStrategy()

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
            strategy: Search strategy to use (default: FUZZY_WORDS)
            
        Returns:
            List of tuples (start, end) where start and end are source tokens indices.
        """
        if isinstance(text, str):
            search_tokens: List[Token] = FulltextSearch.tokenize_text(text)
        else:
            search_tokens: List[Token] = text

        strategy_instance = FulltextSearch._get_strategy(strategy)
        return strategy_instance.search_token_sequences(
            self.source_tokens,
            search_tokens,
            self.dictionary
        )

    def search_all(
        self,
        search_phrases: List[Tuple[str, Union[str, List[Token]]]],
        strategy: Optional[SearchStrategy] = None,
        regex_patterns: Optional[Dict[str, RegexPattern]] = None
    ) -> List[Tuple[str, List[FTSMatch]]]:
        """
        Search all phrases in one pass.
        
        Args:
            search_phrases: List of (phrase_text, text_or_tokens) tuples
            strategy: Search strategy to use (default: FUZZY_WORDS)
            regex_patterns: Optional dictionary of {pattern_name: RegexPattern} for regex-based search
            
        Returns:
            List of (phrase_text, matches) tuples where matches is list of FTSMatch objects
        """
        strategy_instance = FulltextSearch._get_strategy(strategy)
        
        # [start] Optimized path: use dictionary-based search_all_phrases if available
        # This approach uses TokenDictionary to find candidate positions (O(1) lookup)
        # instead of scanning entire text for each phrase, significantly faster for multiple phrases
        if hasattr(strategy_instance, 'search_all_phrases'):
            search_phrases_tokens = []

            for phrase_text, text_or_tokens in search_phrases:
                if isinstance(text_or_tokens, str):
                    search_tokens = FulltextSearch.tokenize_text(text_or_tokens)
                else:
                    search_tokens = text_or_tokens

                search_phrases_tokens.append((phrase_text, search_tokens))

            return strategy_instance.search_all_phrases(
                self.source_tokens,
                search_phrases_tokens,
                self.dictionary,
                regex_patterns=regex_patterns
            )
        # [end]

        # [start] Fallback: search each phrase separately with full text scan
        # This is slower as it calls search() for each phrase, which does full text traversal
        # Used when strategy doesn't implement optimized search_all_phrases method
        results = []

        # Get regex matches if strategy supports them
        regex_matches_map: Dict[Tuple[int, int], RegexPattern] = {}
        if hasattr(strategy_instance, 'search_regex_matches') and regex_patterns:
            regex_matches = strategy_instance.search_regex_matches(
                self.source_tokens,
                regex_patterns=regex_patterns
            )

            for regex_match in regex_matches:
                key = (regex_match.start_token_idx, regex_match.end_token_idx)
                regex_matches_map[key] = regex_match.regex_info

        for phrase_text, text_or_tokens in search_phrases:
            matches_indices = self.search(text_or_tokens, strategy)
            matches = []

            for start, end in matches_indices:
                key = (start, end)

                if key in regex_matches_map:
                    regex_info = regex_matches_map[key]
                    matches.append(FTSRegexMatch(
                        tokens=self.source_tokens[start:end + 1],
                        start_token_idx=start,
                        end_token_idx=end,
                        regex_info=regex_info
                    ))
                else:
                    matches.append(FTSTextMatch(
                        tokens=self.source_tokens[start:end + 1],
                        start_token_idx=start,
                        end_token_idx=end,
                        search_text=phrase_text
                    ))

            results.append((phrase_text, matches))

        return results
        # [end]

    @staticmethod
    def tokenize_text(text: str) -> List[Token]:
        """
        Universal text tokenization for fulltext search.

        Returns list of dictionaries, each containing:
            - 'text': str - token text
            - 'start': int - start position
            - 'end': int - end position
            - 'type': str - token type ('word', 'punct', 'space')
            - 'lemma': str | None - lemma (only for type='word')
            - 'stem': str | None - stem (only for type='word')
        """
        ensure_models_loaded()

        tokens = []
        full_text = text

        if not full_text:
            return tokens

        current_pos = 0

        for match in TOKENIZE_PATTERN_UNIVERSAL.finditer(full_text):
            start, end = match.span()
            text_token = match.group(0)

            if start > current_pos:
                missed_text = full_text[current_pos:start]
                tokens.append(Token(
                    text=missed_text,
                    start=current_pos,
                    end=start,
                    type=TokenType.PUNCTUATION,
                    lemma=None,
                    stem=None
                ))

            token_type = TokenType.PUNCTUATION
            lemma = None
            stem = None

            if match.group(1):
                token_type = TokenType.WORD
                word_lower = text_token.lower()

                if PYMORPHY_AVAILABLE:
                    lemma = pymorphy_service._get_lemma(word_lower)
                    stem = pymorphy_service._get_stem(word_lower)
                else:
                    lemma = pymorphy_service._get_lemma(word_lower)
                    stem = pymorphy_service._get_stem(word_lower)
            elif match.group(3):
                token_type = TokenType.SPACE

            tokens.append(Token(
                text=text_token,
                start=start,
                end=end,
                type=token_type,
                lemma=lemma,
                stem=stem
            ))
            current_pos = end

        if current_pos < len(full_text):
            remaining_text = full_text[current_pos:]
            tokens.append(Token(
                text=remaining_text,
                start=current_pos,
                end=len(full_text),
                type=TokenType.PUNCTUATION,
                lemma=None,
                stem=None
            ))

        return tokens

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
        Works only with FUZZY_WORDS strategy.
        
        Args:
            source_tokens: Tokens from source text
            search_tokens: Tokens from search query
            strategy: Search strategy to use (default: FUZZY_WORDS)
            
        Returns:
            True if sequences match according to strategy, False otherwise
        """
        strategy_instance = FulltextSearch._get_strategy(strategy)
        
        if not isinstance(strategy_instance, FuzzyWordsStrategy):
            raise ValueError("_compare_token_sequences is only available for FUZZY_WORDS strategy")
        
        return strategy_instance._compare_token_sequences(source_tokens, search_tokens)

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
            strategy: Search strategy to use (default: FUZZY_WORDS)
            
        Returns:
            List of tuples (start, end) where start and end are source tokens indices.
        """
        strategy_instance = FulltextSearch._get_strategy(strategy)
        dictionary = TokenDictionary(source_tokens)
        return strategy_instance.search_token_sequences(source_tokens, search_tokens, dictionary)
