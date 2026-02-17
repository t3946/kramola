from services.enum import PredefinedListKey
from services.words_list import WordsList


class ListSwearWords(WordsList):
    key = PredefinedListKey.SWEAR_WORDS.value

    @property
    def list_key(self) -> str:
        return self.key

