from collections import defaultdict
from typing import List, Dict, Set

from services.tokenization.token import Token, TokenType


class TokenDictionary:
    """
    Dictionary for fast token lookup by lemma, stem, and text.
    Provides O(1) lookup for token positions by different attributes.
    """

    def __init__(self, source_tokens: List[Token]) -> None:
        self.lemma_index: Dict[str, List[int]] = defaultdict(list)
        self.stem_index: Dict[str, List[int]] = defaultdict(list)
        self.text_index: Dict[str, List[int]] = defaultdict(list)
        self.text_lower_index: Dict[str, List[int]] = defaultdict(list)
        self.source_tokens = source_tokens

        for i, token in enumerate(source_tokens):
            if token.type == TokenType.WORD:
                if token.lemma:
                    self.lemma_index[token.lemma].append(i)
                if token.stem:
                    self.stem_index[token.stem].append(i)
                self.text_index[token.text].append(i)
                self.text_lower_index[token.text.lower()].append(i)

    def find_candidate_positions(self, token: Token) -> Set[int]:
        candidates: Set[int] = set()
        if token.lemma:
            candidates.update(self.lemma_index.get(token.lemma, []))
        if token.stem:
            candidates.update(self.stem_index.get(token.stem, []))
        if token.text:
            candidates.update(self.text_index.get(token.text, []))
            candidates.update(self.text_lower_index.get(token.text.lower(), []))
        return candidates

    def has_token(self, token: Token) -> bool:
        if token.lemma and token.lemma in self.lemma_index:
            for idx in self.lemma_index[token.lemma]:
                if token.is_equal(self.source_tokens[idx]):
                    return True
        if token.stem and token.stem in self.stem_index:
            for idx in self.stem_index[token.stem]:
                if token.is_equal(self.source_tokens[idx]):
                    return True
        if token.text:
            if token.text in self.text_index:
                return True
            if token.text.lower() in self.text_lower_index:
                return True
        return False

    def filter_tokens(self, tokens: List[Token]) -> List[Token]:
        return [t for t in tokens if self.has_token(t)]
