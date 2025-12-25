from services.words_list import WordsList, PredefinedListKey


class ListProhibitedSubstances(WordsList):
    key = PredefinedListKey.PROHIBITED_SUBSTANCES.value

    @property
    def list_key(self) -> str:
        return self.key

