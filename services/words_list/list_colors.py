from typing import ClassVar
from models.phrase_list.list_record import ListRecord
from services.enum import WordsListKey
from services.utils.color import Color

DEFAULT_LIST_COLOR_HEX: str = "#00ff00"

class ListColor:
    highlight_color: Color
    key: ClassVar[WordsListKey]

    def __init__(self, *args, **kwargs):
        record = ListRecord.query.filter_by(name=self.key.value).first()
        self.highlight_color = Color(record.color) if record else Color(DEFAULT_LIST_COLOR_HEX)

        super().__init__(*args, **kwargs)
