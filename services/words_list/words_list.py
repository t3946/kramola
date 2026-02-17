from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List
from sqlalchemy import func, or_
from extensions import db

from models import ListLog, ListPhrase, ListRecord, PhraseRecord
from services.enum.predefined_list import SearchSourceType
from services.fulltext_search.phrase import Phrase


class WordsList(ABC):
    @property
    @abstractmethod
    def list_key(self) -> str:
        pass

    def _get_list_record(self) -> ListRecord:
        record = ListRecord.query.filter_by(name=self.list_key).first()
        if record is None:
            record = ListRecord(name=self.list_key)
            db.session.add(record)
            db.session.flush()
        return record

    def save(self, words_list: List[str], logging: bool) -> None:
        list_record = self._get_list_record()
        phrases_new_texts = set(words_list)

        if logging:
            phrases_old = self.load()
            phrases_old_texts = {p.phrase for p in phrases_old}
            added_words = list(phrases_new_texts - phrases_old_texts)
            deleted_words = list(phrases_old_texts - phrases_new_texts)
            now = datetime.now()

            for word in deleted_words:
                log_row = ListLog(
                    list_id=list_record.id,
                    phrase=word,
                    add_date=None,
                    remove_date=now,
                )
                db.session.add(log_row)
            for word in added_words:
                log_row = ListLog(
                    list_id=list_record.id,
                    phrase=word,
                    add_date=now,
                    remove_date=None,
                )
                db.session.add(log_row)

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
        return [Phrase(phrase, SearchSourceType.LIST) for (phrase,) in rows]

    def clear(self) -> None:
        list_record = self._get_list_record()
        ListPhrase.query.filter_by(list_id=list_record.id).delete(synchronize_session=False)
        self.clear_log()
        db.session.commit()

    def load_logs(self) -> Dict[str, Dict[str, List[str]]]:
        list_record = self._get_list_record()
        logs = ListLog.query.filter_by(list_id=list_record.id).all()
        logs_by_date: Dict[str, Dict[str, List[str]]] = {}

        for log in logs:
            if log.add_date is not None:
                date_str = log.add_date.strftime("%Y-%m-%d")
                log_type = "added"
                phrase = log.phrase
            else:
                date_str = log.remove_date.strftime("%Y-%m-%d") if log.remove_date else ""
                log_type = "deleted"
                phrase = log.phrase
            if not date_str:
                continue
            if date_str not in logs_by_date:
                logs_by_date[date_str] = {"added": [], "deleted": []}
            logs_by_date[date_str][log_type].append(phrase)

        return logs_by_date

    def get_changes_json(self) -> Dict[str, Dict[str, Any]]:
        logs_by_date = self.load_logs()
        result: Dict[str, Dict[str, Any]] = {}

        for date_str, changes in logs_by_date.items():
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            result[date_str] = {
                "date": date_obj,
                "added": changes.get("added", []),
                "deleted": changes.get("deleted", []),
                "added_count": len(changes.get("added", [])),
                "deleted_count": len(changes.get("deleted", [])),
            }

        return result

    def clear_log(self, dates: List[str] | None = None) -> None:
        list_record = self._get_list_record()
        if dates is None:
            ListLog.query.filter_by(list_id=list_record.id).delete(synchronize_session=False)
        else:
            date_objs = [datetime.strptime(d, "%Y-%m-%d").date() for d in dates]
            ListLog.query.filter(
                ListLog.list_id == list_record.id,
                or_(
                    func.date(ListLog.add_date).in_(date_objs),
                    func.date(ListLog.remove_date).in_(date_objs),
                ),
            ).delete(synchronize_session=False)

        db.session.commit()
