from services.words_list import WordsList


class ListCompanies(WordsList):
    key = "companies"

    @property
    def list_key(self) -> str:
        return self.key

    def save(self, words_list: list[str], logging = False) -> None:
        super().save(words_list, logging)
