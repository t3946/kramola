from extensions import db


class ListPhrase(db.Model):
    __tablename__ = "pl_phrases_lists"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phrase_id = db.Column(db.Integer, db.ForeignKey("pl_phrases.id", ondelete="CASCADE"), nullable=False)
    list_id = db.Column(db.Integer, db.ForeignKey("pl_lists.id", ondelete="CASCADE"), nullable=False)

    phrase_record = db.relationship(
        "PhraseRecord",
        back_populates="lists",
        primaryjoin="ListPhrase.phrase_id == PhraseRecord.id",
        foreign_keys=[phrase_id],
    )
    list_record = db.relationship(
        "ListRecord",
        back_populates="phrases",
        primaryjoin="ListPhrase.list_id == ListRecord.id",
        foreign_keys=[list_id],
    )

    __table_args__ = (db.UniqueConstraint("phrase_id", "list_id", name="unique_phrase_list"),)

    def __repr__(self) -> str:
        return f"<ListPhrase phrase_id={self.phrase_id} list_id={self.list_id}>"
