from typing import List, Dict, Any, Optional
import json

from services.enum.predefined_list import SearchSourceType
from services.tokenization import Token, tokenize_text


class Phrase:
    phrase: str
    phrase_original: Optional[str]
    source: Optional[SearchSourceType]
    tokens: List[Token]
    # full text imagination of search object

    def __init__(
            self,
            phrase: str,
            phrase_original: Optional[str] = None,
            source: Optional[SearchSourceType] = None,
    ) -> None:
        self.source = source
        self.phrase = phrase
        self.phrase_original = phrase_original
        self.tokens = tokenize_text(phrase)

    def _source_to_serializable(self) -> Optional[str]:
        return self.source.value if self.source is not None else None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize Phrase to dictionary."""
        return {
            'phrase': self.phrase,
            'phrase_original': self.phrase_original,
            'tokens': [token.to_dict() for token in self.tokens],
            'source': self.source.value if self.source is not None else None,
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
        raw = data.get('source')
        phrase.source = SearchSourceType(raw) if raw is not None else None
        return phrase

    @staticmethod
    def from_json(json_str: str) -> 'Phrase':
        """Deserialize Phrase from JSON string."""
        data = json.loads(json_str)
        return Phrase.from_dict(data)

