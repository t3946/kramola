from pathlib import Path
from typing import List, Dict, Any, Union
import json

from services.tokenization import Token, tokenize_text

class Phrase:
    phrase: str
    # origin: list class (WordsList/ListInagents), file path (Path), free text (str), or None
    source: Union[object, Path, str, None]
    tokens: List[Token]

    def __init__(
            self,
            phrase: str,
            source: Union[object, Path, str, None] = None,
    ) -> None:
        self.source = source
        self.phrase = phrase
        self.tokens = tokenize_text(phrase)

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

