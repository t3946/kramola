from pathlib import Path
from typing import List

from services.enum import PredefinedListKey
from tests.docx.base_docx_test import BaseDocxTest


class TestProfanityWords2(BaseDocxTest):
    predefined_lists: List[PredefinedListKey] = [PredefinedListKey.PROFANITY]

    @classmethod
    def test_find_profanity_in_docx(cls) -> None:
        instance = cls()
        with instance.init_app().app_context():
            cls.run_test(Path(__file__))


if __name__ == '__main__':
    instance = TestProfanityWords2()
    with instance.init_app().app_context():
        TestProfanityWords2.run_test(Path(__file__))
