from pathlib import Path
from typing import List

from services.words_list import PredefinedListKey
from tests.pdf.base_pdf_long_lists_test import BasePdfLongListsTest


class TestSwearWords(BasePdfLongListsTest):
    # Используем готовые списки нецензурных слов
    predefined_lists: List[PredefinedListKey] = [
        PredefinedListKey.PROFANITY,
        PredefinedListKey.SWEAR_WORDS
    ]
    
    @staticmethod
    def test_find_words_in_pdf() -> None:
        TestSwearWords.run_test(Path(__file__))


if __name__ == '__main__':
    TestSwearWords.test_find_words_in_pdf()

