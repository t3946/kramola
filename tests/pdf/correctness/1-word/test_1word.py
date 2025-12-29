from pathlib import Path

from tests.pdf.correctness.base_pdf_test import BasePdfTest


class TestFindWordsInPdf(BasePdfTest):
    @staticmethod
    def test_find_words_in_pdf() -> None:
        TestFindWordsInPdf.run_test(Path(__file__))


if __name__ == '__main__':
    TestFindWordsInPdf.test_find_words_in_pdf()
