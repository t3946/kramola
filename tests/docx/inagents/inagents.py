from pathlib import Path
from typing import List

from services.enum import PredefinedListKey
from tests.docx.base_docx_test import BaseDocxTest


class TestInagents(BaseDocxTest):
    predefined_lists: List[PredefinedListKey] = [PredefinedListKey.FOREIGN_AGENTS_COMPANIES, PredefinedListKey.FOREIGN_AGENTS_PERSONS]

    @classmethod
    def test_find_inagents_in_docx(cls) -> None:
        instance = cls()
        with instance.init_app().app_context():
            cls.run_test(Path(__file__))


if __name__ == '__main__':
    instance = TestInagents()
    with instance.init_app().app_context():
        TestInagents.run_test(Path(__file__))
