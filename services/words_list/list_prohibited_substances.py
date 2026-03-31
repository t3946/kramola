from services.enum import WordsListKey
from services.words_list import SimpleList


class ListProhibitedSubstances(SimpleList):
    key = WordsListKey.PROHIBITED_SUBSTANCES
    title: str = "Запрещённые вещества"
    description: str = (
        "Перечень наименований наркотических и иных запрещённых веществ, "
        "включая официальные названия, жаргонные обозначения и сленговые формы"
    )
