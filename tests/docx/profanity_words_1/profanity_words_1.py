from pathlib import Path
from typing import List

from services.words_list import PredefinedListKey
from tests.docx.base_docx_test import BaseDocxTest


class TestProfanityWords(BaseDocxTest):
    predefined_lists: List[PredefinedListKey] = [PredefinedListKey.PROFANITY]

    @classmethod
    def test_find_profanity_in_docx(cls) -> None:
        instance = cls()
        with instance.init_app().app_context():
            cls.run_test(Path(__file__))


if __name__ == '__main__':
    instance = TestProfanityWords()
    with instance.init_app().app_context():
        TestProfanityWords.run_test(Path(__file__))
