from pathlib import Path

from tests.pdf.correctness.base_pdf_test import BasePdfTest


class TestWordForms(BasePdfTest):
    @staticmethod
    def test_find_words_in_pdf() -> None:
        TestWordForms.run_test(Path(__file__))


if __name__ == '__main__':
    TestWordForms.test_find_words_in_pdf()
