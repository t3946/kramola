from pathlib import Path

from tests.pdf.base_pdf_long_lists_test import BasePdfLongListsTest


class TestFlLongList(BasePdfLongListsTest):
    @staticmethod
    def test_find_words_in_pdf() -> None:
        TestFlLongList.run_test(Path(__file__))


if __name__ == '__main__':
    TestFlLongList.test_find_words_in_pdf()

