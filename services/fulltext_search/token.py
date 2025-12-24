from typing import Optional
from enum import Enum


class TokenType(Enum):
    WORD = 'word'
    PUNCTUATION = 'punct'
    SPACE = 'space'


class Token:
    text: str
    start: int
    end: int
    type: TokenType
    lemma: Optional[str]
    stem: Optional[str]

    def __init__(
        self,
        text: str,
        start: int,
        end: int,
        type: TokenType,
        lemma: Optional[str] = None,
        stem: Optional[str] = None
    ) -> None:
        self.text = text
        self.start = start
        self.end = end
        self.type = type
        self.lemma = lemma
        self.stem = stem

    def is_equal(self, t2: 'Token') -> bool:
        """
        Check if two tokens are equal by comparing both lemma and stem.

        Args:
            t2: Token to compare with

        Returns:
            True if both lemma and stem match, False otherwise
        """
        lemma_match = self.lemma and t2.lemma and self.lemma == t2.lemma
        stem_match = self.stem and t2.stem and self.stem == t2.stem
        text_match = self.text == t2.text
        
        return text_match or (lemma_match and stem_match)

