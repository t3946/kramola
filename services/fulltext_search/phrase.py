from typing import List
from .fulltext_search import Token, FulltextSearch


class Phrase:
    phrase: str
    tokens: List[Token]

    def __init__(self, phrase: str) -> None:
        self.phrase = phrase
        self.tokens = FulltextSearch.tokenize_text(phrase)

