from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import func, or_

from extensions import db
from models import ListLog


class ListLogs:
    def __init__(self, list_id: int) -> None:
        self._list_id = list_id

    def write_changes(
        self,
        phrases_old_texts: set[str],
        phrases_new_texts: set[str],
    ) -> None:
        added_words = list(phrases_new_texts - phrases_old_texts)
        deleted_words = list(phrases_old_texts - phrases_new_texts)
        now = datetime.now()

        for word in deleted_words:
            log_row = ListLog(
                list_id=self._list_id,
                phrase=word,
                add_date=None,
                remove_date=now,
            )
            db.session.add(log_row)

        for word in added_words:
            log_row = ListLog(
                list_id=self._list_id,
                phrase=word,
                add_date=now,
                remove_date=None,
            )
            db.session.add(log_row)

    def load_logs(self) -> Dict[str, Dict[str, List[str]]]:
        logs = ListLog.query.filter_by(list_id=self._list_id).all()
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

    def clear(self, dates: List[str] | None = None) -> None:
        if dates is None:
            ListLog.query.filter_by(list_id=self._list_id).delete(synchronize_session=False)
        else:
            date_objs = [datetime.strptime(d, "%Y-%m-%d").date() for d in dates]
            ListLog.query.filter(
                ListLog.list_id == self._list_id,
                or_(
                    func.date(ListLog.add_date).in_(date_objs),
                    func.date(ListLog.remove_date).in_(date_objs),
                ),
            ).delete(synchronize_session=False)

        db.session.commit()
