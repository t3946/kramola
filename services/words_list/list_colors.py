from typing import ClassVar

from models.phrase_list.list_record import ListRecord
from services.enum import WordsListKey
from services.utils.color import Color


class ListColor:
    highlight_color: Color
    key: ClassVar[WordsListKey]

    def __init__(self, *args, **kwargs):
        record = ListRecord.query.filter_by(slug=self.key).first()
        self.highlight_color = Color(record.color)

        super().__init__(*args, **kwargs)
