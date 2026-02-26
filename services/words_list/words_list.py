from abc import ABC, abstractmethod
from typing import ClassVar

from services.enum import WordsListKey
from services.words_list.list_colors import ListColor


class WordsList(ListColor, ABC):
    key: ClassVar[WordsListKey]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    @abstractmethod
    def count_phrases(self) -> int:
        """Number of phrases/entries in this list (for admin menu and stats)."""
        pass
