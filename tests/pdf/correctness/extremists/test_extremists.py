from pathlib import Path
from typing import List

from services.enum import PredefinedListKey
from tests.pdf.base_pdf_long_lists_test import BasePdfLongListsTest


class TestExtremists(BasePdfLongListsTest):
    predefined_lists: List[PredefinedListKey] = [
        PredefinedListKey.EXTREMISTS_INTERNATIONAL_FIZ,
        PredefinedListKey.EXTREMISTS_INTERNATIONAL_UR,
        PredefinedListKey.EXTREMISTS_RUSSIAN_FIZ,
        PredefinedListKey.EXTREMISTS_RUSSIAN_UR,
    ]

    @classmethod
    def test_find_extremists_in_pdf(cls) -> None:
        instance = cls()

        with instance.init_app().app_context():
            cls.run_test(Path(__file__))


if __name__ == '__main__':
    TestExtremists.test_find_extremists_in_pdf()
