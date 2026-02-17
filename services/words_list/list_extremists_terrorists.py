from services.enum import PredefinedListKey
from services.words_list import WordsList


class ListExtremistsTerrorists(WordsList):
    key = PredefinedListKey.EXTREMISTS_TERRORISTS.value

    @property
    def list_key(self) -> str:
        return self.key
