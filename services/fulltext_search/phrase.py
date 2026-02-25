from typing import List, Dict, Any, Optional
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
