from extensions import db


class ListLog(db.Model):
    __tablename__ = "pl_lists_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    list_id = db.Column(db.Integer, db.ForeignKey("pl_lists.id", ondelete="CASCADE"), nullable=False)
    phrase = db.Column(db.String(500), nullable=False)
    add_date = db.Column(db.TIMESTAMP, nullable=True)
    remove_date = db.Column(db.TIMESTAMP, nullable=True)

    list_record = db.relationship(
        "ListRecord",
        back_populates="logs",
        primaryjoin="ListLog.list_id == ListRecord.id",
        foreign_keys=[list_id],
    )

    def __repr__(self) -> str:
        return f"<ListLog list_id={self.list_id} phrase={self.phrase!r}>"
