from typing import List, Dict, Any, Optional
import json

from services.enum.predefined_list import ESearchSource
from services.tokenization import Token, tokenize_text
from services.words_list.words_list import WordsList


class Phrase:
    phrase: str
    phrase_original: Optional[str]
    source_list: WordsList
    tokens: List[Token]
    # full text imagination of search object

    def __init__(
            self,
            phrase: str,
            source_list: WordsList,
            phrase_original: Optional[str] = None,
    ) -> None:
        self.source_list = source_list
        self.phrase = phrase
        self.phrase_original = phrase_original
        self.tokens = tokenize_text(phrase)

    def _source_to_serializable(self) -> Optional[str]:
        return self.source_list.key

    def to_dict(self) -> Dict[str, Any]:
        """Serialize Phrase to dictionary."""
        return {
            'phrase': self.phrase,
            'phrase_original': self.phrase_original,
            'tokens': [token.to_dict() for token in self.tokens],
            'source_list': self.source_list.key.value if self.source_list is not None else None,
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
        raw = data.get('source_list')
        phrase.source_list = ESearchSource(raw) if raw is not None else None
        return phrase

    @staticmethod
    def from_json(json_str: str) -> 'Phrase':
        """Deserialize Phrase from JSON string."""
        data = json.loads(json_str)
        return Phrase.from_dict(data)

