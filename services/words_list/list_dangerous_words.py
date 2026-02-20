from services.enum import PredefinedListKey
from services.words_list import WordsList


class ListDangerousWords(WordsList):
    key = PredefinedListKey.DANGEROUS_WORDS.value

    @property
    def list_key(self) -> str:
        return self.key
