from pathlib import Path

from tests.docx.base_docx_test import BaseDocxTest


class TestFindSentencesInDocx(BaseDocxTest):
    @staticmethod
    def test_find_sentences_in_docx() -> None:
        TestFindSentencesInDocx.run_test(Path(__file__))


if __name__ == '__main__':
    TestFindSentencesInDocx.run_test(Path(__file__))
