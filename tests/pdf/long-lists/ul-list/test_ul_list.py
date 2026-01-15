from pathlib import Path

from tests.pdf.base_pdf_long_lists_test import BasePdfLongListsTest


class TestUlListLongList(BasePdfLongListsTest):
    @staticmethod
    def test_find_words_in_pdf() -> None:
        TestUlListLongList.run_test(Path(__file__))


if __name__ == '__main__':
    TestUlListLongList.test_find_words_in_pdf()

