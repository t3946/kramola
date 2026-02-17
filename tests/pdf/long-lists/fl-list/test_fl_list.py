from pathlib import Path
from typing import List

from services.enum import PredefinedListKey
from tests.pdf.base_pdf_long_lists_test import BasePdfLongListsTest


class TestFlListLongList(BasePdfLongListsTest):
    # Используем готовый список физических лиц
    predefined_lists: List[PredefinedListKey] = [
        PredefinedListKey.FOREIGN_AGENTS_PERSONS
    ]
    
    @staticmethod
    def test_find_words_in_pdf() -> None:
        TestFlListLongList.run_test(Path(__file__))


if __name__ == '__main__':
    TestFlListLongList.test_find_words_in_pdf()

