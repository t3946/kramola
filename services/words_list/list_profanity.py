from services.enum import PredefinedListKey
from services.words_list import WordsList


class ListProfanity(WordsList):
    key = PredefinedListKey.PROFANITY.value

    @property
    def list_key(self) -> str:
        return self.key

