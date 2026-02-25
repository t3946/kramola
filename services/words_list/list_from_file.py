from typing import List

from services.enum.predefined_list import ESearchSource
from services.utils.load_lines_from_txt import load_lines_from_txt
from services.words_list.list_user_custom import ListUserCustom


class ListFromFile(ListUserCustom):
    """Phrases loaded from a text file (one phrase per line)."""

    def __init__(self, filepath: str) -> None:
        self._filepath = filepath
        super().__init__()

    @property
    def source(self) -> ESearchSource:
        return ESearchSource.FILE

    def _get_phrases(self) -> List[str]:
        return load_lines_from_txt(self._filepath)
