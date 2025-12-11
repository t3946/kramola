from services.words_list import WordsList


class ListCompanies(WordsList):
    key = "companies"

    @property
    def list_key(self) -> str:
        return self.key
