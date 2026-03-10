from pathlib import Path

from tests.docx.base_docx_test import BaseDocxTest


class TestFindSentencesInDocx(BaseDocxTest):
    @classmethod
    def test_find_sentences_in_docx(cls) -> None:
        instance = cls()
        with instance.init_app().app_context():
            TestFindSentencesInDocx.run_test(Path(__file__))


if __name__ == '__main__':
    instance = TestFindSentencesInDocx()
    with instance.init_app().app_context():
        TestFindSentencesInDocx.run_test(Path(__file__))
