from services.words_list import WordsList, PredefinedListKey


class ListSwearWords(WordsList):
    key = PredefinedListKey.SWEAR_WORDS.value

    @property
    def list_key(self) -> str:
        return self.key

