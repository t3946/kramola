from services.enum import PredefinedListKey
from services.words_list import SimpleList


class ListProhibitedSubstances(SimpleList):
    key = PredefinedListKey.PROHIBITED_SUBSTANCES.value
