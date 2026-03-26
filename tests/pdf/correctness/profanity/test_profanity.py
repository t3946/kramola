from pathlib import Path
from typing import List

from services.enum import PredefinedListKey
from tests.pdf.base_pdf_long_lists_test import BasePdfLongListsTest


class TestProfanity(BasePdfLongListsTest):
    predefined_lists: List[PredefinedListKey] = [
        PredefinedListKey.PROFANITY,
    ]

    @classmethod
    def test_find_extremists_in_pdf(cls) -> None:
        instance = cls()

        with instance.init_app().app_context():
            cls.run_test(Path(__file__))


if __name__ == '__main__':
    TestProfanity.test_find_extremists_in_pdf()
