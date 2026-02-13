import re
from typing import List

from services import pymorphy_service
from services.pymorphy_service import ensure_models_loaded

from services.tokenization.token import Token, TokenType


class Tokenizer:
    TOKENIZE_PATTERN = re.compile(r"(\w+)|([^\w\s]+)|(\s+)", re.UNICODE)

    @staticmethod
    def tokenize_text(text: str) -> List[Token]:
        """
        Universal text tokenization.

        Returns list of Token with text, start, end, type ('word', 'punct', 'space'),
        lemma and stem for words.
        """
        ensure_models_loaded()

        tokens: List[Token] = []
        if not text:
            return tokens

        current_pos = 0

        for match in Tokenizer.TOKENIZE_PATTERN.finditer(text):
            start, end = match.span()
            text_token = match.group(0)

            if start > current_pos:
                missed_text = text[current_pos:start]
                tokens.append(Token(
                    text=missed_text,
                    start=current_pos,
                    end=start,
                    type=TokenType.PUNCTUATION,
                    lemma=None,
                    stem=None
                ))

            token_type = TokenType.PUNCTUATION
            lemma = None
            stem = None

            if match.group(1):
                token_type = TokenType.WORD
                word_lower = text_token.lower()
                lemma = pymorphy_service._get_lemma(word_lower)
                stem = pymorphy_service._get_stem(word_lower)
            elif match.group(3):
                token_type = TokenType.SPACE

            tokens.append(Token(
                text=text_token,
                start=start,
                end=end,
                type=token_type,
                lemma=lemma,
                stem=stem
            ))
            current_pos = end

        if current_pos < len(text):
            remaining_text = text[current_pos:]
            tokens.append(Token(
                text=remaining_text,
                start=current_pos,
                end=len(text),
                type=TokenType.PUNCTUATION,
                lemma=None,
                stem=None
            ))

        return tokens


tokenize_text = Tokenizer.tokenize_text
