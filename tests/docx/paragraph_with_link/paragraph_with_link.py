from pathlib import Path

from tests.docx.base_docx_test import BaseDocxTest


class TestParagraphWithLink(BaseDocxTest):
    @staticmethod
    def test_find_sentences_in_docx() -> None:
        TestParagraphWithLink.run_test(Path(__file__))


if __name__ == '__main__':
    TestParagraphWithLink.run_test(Path(__file__))
