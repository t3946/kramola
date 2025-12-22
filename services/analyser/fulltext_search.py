import re
from enum import Enum
from typing import List, Optional, TypedDict, Tuple
from services.pymorphy_service import _get_lemma, _get_stem, CYRILLIC_PATTERN, ensure_models_loaded
from services import pymorphy_service
from services.analyser.strategies import FuzzyWordsStrictOrderStrategy

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


class Token(TypedDict):
    text: str
    start: int
    end: int
    type: str
    lemma: Optional[str]
    stem: Optional[str]


class Match(TypedDict):
    type: str
    start_token_idx: int
    end_token_idx: int
    lemma_key: Tuple[str, ...]
    match_type: str


class SearchStrategy(Enum):
    """Search strategy enum."""
    FUZZY_WORDS_STRICT_ORDER = "fuzzy_words_strict_order"
    STRICT_ORDER_FUZZY_PUNCT = "strict_order_fuzzy_punct"


class FulltextSearch:
    """
    Implements fulltext search algorithms.

    Provides methods for text tokenization and matching
    by words and phrases using lemmatization and stemming.
    """

    _default_strategy = FuzzyWordsStrictOrderStrategy()

    @staticmethod
    def _get_strategy(strategy: Optional[SearchStrategy] = None):
        """Get strategy instance by enum value."""
        if strategy is None:
            return FulltextSearch._default_strategy

        if strategy == SearchStrategy.FUZZY_WORDS_STRICT_ORDER:
            return FuzzyWordsStrictOrderStrategy()
        elif strategy == SearchStrategy.STRICT_ORDER_FUZZY_PUNCT:
            raise NotImplementedError("STRICT_ORDER_FUZZY_PUNCT strategy not implemented yet")

        return FulltextSearch._default_strategy

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
                tokens.append({
                    'text': missed_text,
                    'start': current_pos,
                    'end': start,
                    'type': 'punct',
                    'lemma': None,
                    'stem': None
                })

            token_type = 'punct'
            lemma = None
            stem = None

            if match.group(1):
                token_type = 'word'
                word_lower = text_token.lower()

                if PYMORPHY_AVAILABLE:
                    lemma = pymorphy_service._get_lemma(word_lower)
                    stem = pymorphy_service._get_stem(word_lower)
                else:
                    lemma = pymorphy_service._get_lemma(word_lower)
                    stem = pymorphy_service._get_stem(word_lower)
            elif match.group(3):
                token_type = 'space'

            tokens.append({
                'text': text_token,
                'start': start,
                'end': end,
                'type': token_type,
                'lemma': lemma,
                'stem': stem
            })
            current_pos = end

        if current_pos < len(full_text):
            remaining_text = full_text[current_pos:]
            tokens.append({
                'text': remaining_text,
                'start': current_pos,
                'end': len(full_text),
                'type': 'punct',
                'lemma': None,
                'stem': None
            })

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
        Works only with FUZZY_WORDS_STRICT_ORDER strategy.
        
        Args:
            source_tokens: Tokens from source text
            search_tokens: Tokens from search query
            strategy: Search strategy to use (default: FUZZY_WORDS_STRICT_ORDER)
            
        Returns:
            True if sequences match according to strategy, False otherwise
        """
        strategy_instance = FulltextSearch._get_strategy(strategy)
        
        if not isinstance(strategy_instance, FuzzyWordsStrictOrderStrategy):
            raise ValueError("_compare_token_sequences is only available for FUZZY_WORDS_STRICT_ORDER strategy")
        
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
            strategy: Search strategy to use (default: FUZZY_WORDS_STRICT_ORDER)
            
        Returns:
            List of tuples (start, end) where start and end are source tokens indices.
        """
        strategy_instance = FulltextSearch._get_strategy(strategy)
        return strategy_instance.search_token_sequences(source_tokens, search_tokens)
