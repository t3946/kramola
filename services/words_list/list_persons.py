from services.words_list import WordsList


class ListPersons(WordsList):
    key = "persons"

    @property
    def list_key(self) -> str:
        return self.key

    def save(self, words_list: list[str], options) -> None:
        super().save(words_list, options)
