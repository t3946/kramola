from extensions import db


class PhraseRecord(db.Model):
    __tablename__ = "pl_phrases"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phrase = db.Column(db.String(200), unique=True, nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=True)

    lists = db.relationship(
        "ListPhrase",
        back_populates="phrase_record",
        primaryjoin="PhraseRecord.id == ListPhrase.phrase_id",
        foreign_keys="ListPhrase.phrase_id",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<PhraseRecord {self.phrase!r}>"
