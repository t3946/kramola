from services.enum import PredefinedListKey
from services.words_list import WordsList


class ListCompanies(WordsList):
    key = PredefinedListKey.FOREIGN_AGENTS_COMPANIES.value

    @property
    def list_key(self) -> str:
        return self.key
