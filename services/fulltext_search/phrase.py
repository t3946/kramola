from enum import Enum
from typing import List, Dict, Any, Optional
from extensions import db

from services.tokenization import Token, Tokenizer

class EType(Enum):
    TEXT = 'text'
    SURNAME = 'surname'
    FULL_NAME = 'full_name'

class Phrase:
    phrase: str
    phrase_original: Optional[str]
    source_list: "WordsList"
    tokens: List[Token]
    phrase_type: EType
    model: db.Model
    # full text imagination of search object

    def __init__(
            self,
            phrase: str,
            source_list: Optional["WordsList"] = None,
            phrase_original: Optional[str] = None,
            phrase_type: EType = EType.TEXT,
            model: db.Model = None,
    ) -> None:
        self.source_list = source_list
        self.phrase = phrase
        self.phrase_original = phrase_original
        self.tokens = Tokenizer(None).tokenize_text(phrase)
        self.phrase_type = phrase_type
        self.model = model

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

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Phrase":
        """Deserialize Phrase from dictionary (source_list not restored)."""
        return Phrase(
            phrase=data["phrase"],
            phrase_original=data.get("phrase_original"),
            source_list=None,
        )
