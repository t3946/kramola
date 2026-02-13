from enum import Enum
from typing import Any, Dict, Optional


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
        lemma_match = self.lemma and t2.lemma and self.lemma == t2.lemma
        stem_match = self.stem and t2.stem and self.stem == t2.stem
        text_match = self.text == t2.text
        return text_match or (lemma_match and stem_match)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'text': self.text,
            'start': self.start,
            'end': self.end,
            'type': self.type.value,
            'lemma': self.lemma,
            'stem': self.stem
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Token':
        return Token(
            text=data['text'],
            start=data['start'],
            end=data['end'],
            type=TokenType(data['type']),
            lemma=data.get('lemma'),
            stem=data.get('stem')
        )
