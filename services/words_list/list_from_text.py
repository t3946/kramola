from typing import List

from services.fulltext_search.phrase import Phrase
from services.words_list.list_user_custom import ListUserCustom


class ListFromText(ListUserCustom):
    """Phrases passed as text (lines split by newline)."""

    def __init__(self) -> None:
        super().__init__()

    def load_from_lines(self, lines: List[str]) -> List[Phrase]:
        phrases: List[Phrase] = []

        for text in lines:
            phrases.append(Phrase(text, source_list=self.source))

        return phrases
