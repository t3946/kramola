from pathlib import Path

from tests.docx.base_docx_test import BaseDocxTest


class TestProfanityWords(BaseDocxTest):
    @staticmethod
    def test_find_profanity_in_docx() -> None:
        TestProfanityWords.run_test(Path(__file__))


if __name__ == '__main__':
    TestProfanityWords.run_test(Path(__file__))
