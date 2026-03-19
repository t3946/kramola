from services.fulltext_search.strategies.base_strategy import BaseSearchStrategy
from services.fulltext_search.strategies.fuzzy_words import FuzzyWordsStrategy
from services.fulltext_search.strategies.fuzzy_words_punct import FuzzyWordsPunctStrategy
from services.fulltext_search.strategies.surname_strategy.surname_strategy import SurnameStrategy

__all__ = [
    'BaseSearchStrategy',
    'FuzzyWordsStrategy',
    'FuzzyWordsPunctStrategy',
    'SurnameStrategy',
]
