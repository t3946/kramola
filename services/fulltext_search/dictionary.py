from typing import List, Dict, Set, TYPE_CHECKING
from collections import defaultdict

if TYPE_CHECKING:
    from services.fulltext_search.fulltext_search import Token


class TokenDictionary:
    """
    Dictionary for fast token lookup by lemma, stem, and text.
    
    Provides O(1) lookup for token positions by different attributes.
    """

    def __init__(self, source_tokens: 'List[Token]'):
        """
        Build dictionary from source tokens.
        
        Args:
            source_tokens: List of tokens to index
        """
        self.lemma_index: Dict[str, List[int]] = defaultdict(list)
        self.stem_index: Dict[str, List[int]] = defaultdict(list)
        self.text_index: Dict[str, List[int]] = defaultdict(list)
        self.source_tokens = source_tokens

        for i, token in enumerate(source_tokens):
            if token['type'] == 'word':
                if token['lemma']:
                    self.lemma_index[token['lemma']].append(i)
                if token['stem']:
                    self.stem_index[token['stem']].append(i)
                self.text_index[token['text']].append(i)

    def find_candidate_positions(self, token: 'Token') -> Set[int]:
        """
        Find all positions where token can match.
        
        Args:
            token: Token to search for
            
        Returns:
            Set of token indices where this token might match
        """
        candidates = set()

        if token['lemma']:
            candidates.update(self.lemma_index.get(token['lemma'], []))
        if token['stem']:
            candidates.update(self.stem_index.get(token['stem'], []))
        if token['text']:
            candidates.update(self.text_index.get(token['text'], []))

        return candidates
