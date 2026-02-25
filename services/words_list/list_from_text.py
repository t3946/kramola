from typing import List

from services.enum.predefined_list import ESearchSource
from services.words_list.list_user_custom import ListUserCustom


class ListFromText(ListUserCustom):
    """Phrases passed as text (lines split by newline)."""

    def __init__(self, text: str) -> None:
        self._lines = [line.strip() for line in text.splitlines() if line.strip()]
        super().__init__()

    @property
    def source(self) -> ESearchSource:
        return ESearchSource.TEXT

    def _get_phrases(self) -> List[str]:
        return self._lines
