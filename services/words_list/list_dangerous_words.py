from services.enum import PredefinedListKey
from services.words_list import SimpleList


class ListDangerousWords(SimpleList):
    key = PredefinedListKey.DANGEROUS_WORDS.value
