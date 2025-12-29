from pathlib import Path

from tests.pdf.correctness.base_pdf_test import BasePdfTest


class TestFindSentencesInPdf(BasePdfTest):
    @staticmethod
    def test_find_sentences_in_pdf() -> None:
        TestFindSentencesInPdf.run_test(Path(__file__))


if __name__ == '__main__':
    TestFindSentencesInPdf.test_find_sentences_in_pdf()
