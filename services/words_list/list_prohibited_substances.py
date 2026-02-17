from services.enum import PredefinedListKey
from services.words_list import WordsList


class ListProhibitedSubstances(WordsList):
    key = PredefinedListKey.PROHIBITED_SUBSTANCES.value

    @property
    def list_key(self) -> str:
        return self.key

