from models.phrase_list.list_record import ListRecord
from services.utils.color import Color


class ListColor:
    highlight_color: Color
    key: str

    def __init__(self, *args, **kwargs):
        record = ListRecord.query.filter_by(slug=self.key).first()
        self.highlight_color = Color(record.color)

        super().__init__(*args, **kwargs)

    def get_color(self) -> str:
        return (
            ListRecord
            .query
            .filter_by(slug=self.key)
            .first()
            .color
        )

    @staticmethod
    def get_color_by_slug(slug: str) -> str:
        record = ListRecord.query.filter_by(slug=slug).first()
        return record.color if record else ""
