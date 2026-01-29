from extensions import db


class ListRecord(db.Model):
    __tablename__ = "pl_lists"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=True)

    phrases = db.relationship(
        "ListPhrase",
        back_populates="list_record",
        primaryjoin="ListRecord.id == ListPhrase.list_id",
        foreign_keys="ListPhrase.list_id",
        cascade="all, delete-orphan",
    )
    logs = db.relationship(
        "ListLog",
        back_populates="list_record",
        primaryjoin="ListRecord.id == ListLog.list_id",
        foreign_keys="ListLog.list_id",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ListRecord {self.name}>"
