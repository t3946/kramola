from abc import ABC
from typing import ClassVar

from services.enum import WordsListKey
from services.words_list.list_colors import ListColor


class WordsList(ListColor, ABC):
    key: ClassVar[WordsListKey]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
