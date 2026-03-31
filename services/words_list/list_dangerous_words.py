from services.enum import WordsListKey
from services.words_list import SimpleList


class ListDangerousWords(SimpleList):
    key = WordsListKey.DANGEROUS
    title: str = "Опасные слова"
    description: str = (
        "Перечень слов и выражений, связанных с чувствительными и потенциально "
        "нежелательными для публикации темами, включая суицид, аборты и вопросы сексуальной идентичности"
    )
