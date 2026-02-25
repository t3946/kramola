from abc import ABC, abstractmethod
from typing import List

from extensions import db

from models import ListPhrase, ListRecord, PhraseRecord
from services.fulltext_search.phrase import Phrase
from services.words_list.list_logs import ListLogs
from services.words_list.words_list import WordsList


class SimpleList(ABC, WordsList):
    def __init__(self) -> None:
        super().__init__()

    def _get_list_record(self) -> ListRecord:
        record = ListRecord.query.filter_by(name=self.key).first()
        if record is None:
            record = ListRecord(name=self.key)
            db.session.add(record)
            db.session.flush()
        return record

    def save(self, words_list: List[str], logging: bool) -> None:
        list_record = self._get_list_record()
        phrases_new_texts = set(words_list)

        if logging:
            phrases_old = self.load()
            phrases_old_texts = {p.phrase for p in phrases_old}
            ListLogs(list_record.id).write_changes(phrases_old_texts, phrases_new_texts)

        ListPhrase.query.filter_by(list_id=list_record.id).delete(synchronize_session=False)

        # unique (phrase_id, list_id) — skip if same phrase_record already linked (e.g. collation)
        linked_phrase_ids: set[int] = set()
        for word in phrases_new_texts:
            phrase_record = PhraseRecord.query.filter_by(phrase=word).first()
            if phrase_record is None:
                phrase_record = PhraseRecord(phrase=word)
                db.session.add(phrase_record)
                db.session.flush()
            if phrase_record.id in linked_phrase_ids:
                continue
            linked_phrase_ids.add(phrase_record.id)
            link = ListPhrase(phrase_id=phrase_record.id, list_id=list_record.id)
            db.session.add(link)

        db.session.commit()

    def load(self) -> List[Phrase]:
        list_record = self._get_list_record()
        rows = (
            ListPhrase.query.filter_by(list_id=list_record.id)
            .join(PhraseRecord, ListPhrase.phrase_id == PhraseRecord.id)
            .with_entities(PhraseRecord.phrase)
            .all()
        )

        return [Phrase(phrase=phrase, source_list=self) for (phrase,) in rows]

    def clear(self) -> None:
        list_record = self._get_list_record()
        ListPhrase.query.filter_by(list_id=list_record.id).delete(synchronize_session=False)
        ListLogs(list_record.id).clear()
        db.session.commit()
