from services.words_list import WordsList, PredefinedListKey


class ListPersons(WordsList):
    key = PredefinedListKey.FOREIGN_AGENTS_PERSONS.value

    @property
    def list_key(self) -> str:
        return self.key
