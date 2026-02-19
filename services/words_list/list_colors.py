from models.phrase_list.list_record import ListRecord


class ListColor:
    def __init__(self, key: str) -> None:
        self.key = key

    def get_color(self) -> str:
        return (
            ListRecord
            .query
            .filter_by(slug=self.key)
            .first()
            .color
        )
