from services.words_list import WordsList, PredefinedListKey


class ListExtremistsTerrorists(WordsList):
    key = PredefinedListKey.EXTREMISTS_TERRORISTS.value

    @property
    def list_key(self) -> str:
        return self.key
