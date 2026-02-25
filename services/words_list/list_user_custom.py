from abc import ABC

from services.enum import WordsListKey
from services.words_list.words_list import WordsList


class ListUserCustom(WordsList, ABC):
    """User-defined phrase set (from file or text). In-memory, no DB persistence."""

    key = WordsListKey.CUSTOM
