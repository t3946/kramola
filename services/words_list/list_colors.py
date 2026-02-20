from models.phrase_list.list_record import ListRecord


class ListColor:
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
