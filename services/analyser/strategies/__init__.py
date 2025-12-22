from services.analyser.strategies.base_strategy import BaseSearchStrategy
from services.analyser.strategies.fuzzy_words_strict_order import FuzzyWordsStrictOrderStrategy
from services.analyser.strategies.strict_order_fuzzy_punct import StrictOrderFuzzyPunctStrategy

__all__ = [
    'BaseSearchStrategy',
    'FuzzyWordsStrictOrderStrategy',
    'StrictOrderFuzzyPunctStrategy'
]
