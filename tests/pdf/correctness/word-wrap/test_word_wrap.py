from pathlib import Path

from tests.pdf.correctness.base_pdf_test import BasePdfTest


class TestWordWrap(BasePdfTest):
    @staticmethod
    def test_find_words_in_pdf() -> None:
        TestWordWrap.run_test(Path(__file__))


if __name__ == '__main__':
    TestWordWrap.test_find_words_in_pdf()
