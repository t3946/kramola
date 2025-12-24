from typing import List, Dict, Any
import json
from .token import Token
from .fulltext_search import FulltextSearch


class Phrase:
    phrase: str
    tokens: List[Token]

    def __init__(self, phrase: str) -> None:
        self.phrase = phrase
        self.tokens = FulltextSearch.tokenize_text(phrase)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize Phrase to dictionary."""
        return {
            'phrase': self.phrase,
            'tokens': [token.to_dict() for token in self.tokens]
        }

    def to_json(self) -> str:
        """Serialize Phrase to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Phrase':
        """Deserialize Phrase from dictionary."""
        phrase = Phrase.__new__(Phrase)
        phrase.phrase = data['phrase']
        phrase.tokens = [Token.from_dict(token_data) for token_data in data['tokens']]
        return phrase

    @staticmethod
    def from_json(json_str: str) -> 'Phrase':
        """Deserialize Phrase from JSON string."""
        data = json.loads(json_str)
        return Phrase.from_dict(data)

