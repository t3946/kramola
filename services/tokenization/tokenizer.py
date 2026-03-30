import re
from typing import List, Optional

from services import pymorphy_service
from services.pymorphy_service import ensure_models_loaded
from services.progress.combined_progress.combined_progress import CombinedProgress

from services.tokenization.token import Token, TokenType
from services.utils.normalize_text import normalize_text


class Tokenizer:
    """
    Text tokenizer; reports tokenization progress as 0–100% on CombinedProgress when provided.
    Intermediate updates are throttled (every PROGRESS_REPORT_EVERY_N_WORDS words); final % is always sent.
    """

    TOKENIZE_PATTERN = re.compile(r"(\w+)|([^\w\s]+)|(\s+)", re.UNICODE)
    PARTICLE_KEY: str = "tokenization"
    PROGRESS_REPORT_EVERY_N_WORDS: int = 1000 * 10

    def __init__(self, combined_progress: Optional[CombinedProgress] = None) -> None:
        self._combined_progress: Optional[CombinedProgress] = combined_progress

    def _report_tokenize_progress(self, end_exclusive: int, text_len: int) -> None:
        if self._combined_progress is None:
            return

        if text_len <= 0:
            percent: float = 100.0
        else:
            covered: int = min(end_exclusive, text_len)
            percent = 100.0 * float(covered) / float(text_len)

        self._combined_progress.set_particle_value(
            Tokenizer.PARTICLE_KEY,
            percent,
        )

    def tokenize_text(self, text: str) -> List[Token]:
        """
        Universal text tokenization.

        Returns list of Token with text, start, end, type ('word', 'punct', 'space'),
        lemma and stem for words.
        """
        ensure_models_loaded()

        tokens: List[Token] = []

        if not text:
            self._report_tokenize_progress(0, 0)

            return tokens

        text_len: int = len(text)

        current_pos = 0
        words_processed: int = 0

        for match in Tokenizer.TOKENIZE_PATTERN.finditer(text):
            start, end = match.span()
            text_token: str = (
                match
                .group(0)
                .replace("Ё", "Е")
                .replace("ё", "е")
                .lower()
            )

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

            if token_type == TokenType.WORD:
                words_processed += 1

                if (
                    self._combined_progress is not None
                    and words_processed % Tokenizer.PROGRESS_REPORT_EVERY_N_WORDS == 0
                ):
                    self._report_tokenize_progress(current_pos, text_len)

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
            current_pos = len(text)

        if self._combined_progress is not None:
            self._report_tokenize_progress(current_pos, text_len)

        return tokens
