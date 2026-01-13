from pathlib import Path

from tests.pdf.correctness.base_pdf_test import BasePdfTest


class Test400Pages(BasePdfTest):
    @staticmethod
    def test_find_sentences_in_pdf() -> None:
        Test400Pages.run_test(Path(__file__))


if __name__ == '__main__':
    Test400Pages.test_find_sentences_in_pdf()
