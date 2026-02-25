from abc import ABC, abstractmethod
from typing import List

from services.enum.predefined_list import ESearchSource
from services.fulltext_search.phrase import Phrase
from services.words_list.words_list import WordsList


class ListUserCustom(WordsList, ABC):
    """User-defined phrase set (from file or text). In-memory, no DB persistence."""
    @property
    def list_key(self) -> str:
        return self.key
