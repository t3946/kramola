from pathlib import Path
from typing import List

from services.words_list import PredefinedListKey
from tests.pdf.base_pdf_long_lists_test import BasePdfLongListsTest


class TestProfanityWords(BasePdfLongListsTest):
    predefined_lists: List[PredefinedListKey] = [
        PredefinedListKey.PROFANITY,
        PredefinedListKey.SWEAR_WORDS
    ]
    
    @staticmethod
    def test_find_words_in_pdf() -> None:
        TestProfanityWords.run_test(Path(__file__))


if __name__ == '__main__':
    TestProfanityWords.test_find_words_in_pdf()

