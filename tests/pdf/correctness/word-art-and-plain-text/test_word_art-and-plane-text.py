from pathlib import Path

from tests.pdf.correctness.base_pdf_test import BasePdfTest


class TestWordArtAndPlaneText(BasePdfTest):
    @staticmethod
    def test_find_words_in_pdf() -> None:
        TestWordArtAndPlaneText.run_test(Path(__file__))


if __name__ == '__main__':
    TestWordArtAndPlaneText.test_find_words_in_pdf()
