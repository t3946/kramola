from services.enum import WordsListKey
from services.words_list import SimpleList


class ListDangerousWords(SimpleList):
    key = WordsListKey.DANGEROUS_WORDS
