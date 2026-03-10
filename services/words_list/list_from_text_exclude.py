from services.enum import WordsListKey
from services.words_list import ListFromText


class ListFromTextExclude(ListFromText):
    """Exclude phrases passed as text (lines split by newline). Same mechanics as ListFromText."""
    key = WordsListKey.CUSTOM_EXCLUDE

    _redis_key: str = "exclude_terms_json"