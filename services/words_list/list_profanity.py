from services.words_list import WordsList, PredefinedListKey


class ListProfanity(WordsList):
    key = PredefinedListKey.PROFANITY.value

    @property
    def list_key(self) -> str:
        return self.key

