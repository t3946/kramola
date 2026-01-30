from extensions import db
from models.phrase_list.list_phrase import ListPhrase
from models.phrase_list.list_record import ListRecord
from models.phrase_list.phrase_record import PhraseRecord


def get_phrases_sorted(list_record: ListRecord | None) -> list[PhraseRecord]:
    if not list_record:
        return []
    return (
        PhraseRecord.query.join(ListPhrase)
        .filter(ListPhrase.list_id == list_record.id)
        .order_by(PhraseRecord.phrase.asc())
        .all()
    )


def _lines_from_uploaded_file(file) -> list[str]:
    content = file.read()
    if isinstance(content, bytes):
        content = content.decode("utf-8-sig")
    return [line.strip() for line in content.splitlines() if line.strip()]


def import_phrases_from_file(list_record: ListRecord, file) -> int:
    lines: list[str] = _lines_from_uploaded_file(file)
    added = 0
    for phrase_text in lines:
        phrase_record = PhraseRecord.query.filter_by(phrase=phrase_text).first()
        if not phrase_record:
            phrase_record = PhraseRecord(phrase=phrase_text)
            db.session.add(phrase_record)
            db.session.flush()
        link = ListPhrase.query.filter_by(
            phrase_id=phrase_record.id,
            list_id=list_record.id,
        ).first()
        if not link:
            db.session.add(ListPhrase(phrase_id=phrase_record.id, list_id=list_record.id))
            added += 1
    db.session.commit()
    return added


def minusate_phrases_from_file(list_record: ListRecord, file) -> int:
    lines: list[str] = _lines_from_uploaded_file(file)
    removed = 0
    for phrase_text in lines:
        phrase_record = PhraseRecord.query.filter_by(phrase=phrase_text).first()
        if not phrase_record:
            continue
        link = ListPhrase.query.filter_by(
            phrase_id=phrase_record.id,
            list_id=list_record.id,
        ).first()
        if link:
            db.session.delete(link)
            removed += 1
    db.session.commit()
    return removed


def update_phrase_in_list(list_record: ListRecord, phrase_id: int, new_text: str) -> str | None:
    new_text = new_text.strip()
    if not new_text:
        return "Фраза не может быть пустой"
    link = ListPhrase.query.filter_by(list_id=list_record.id, phrase_id=phrase_id).first()
    if not link:
        return "Фраза не найдена в списке"
    existing = PhraseRecord.query.filter_by(phrase=new_text).first()
    if existing and existing.id != phrase_id:
        return "Фраза уже существует"
    phrase_record = PhraseRecord.query.get(phrase_id)
    if not phrase_record:
        return "Фраза не найдена"
    phrase_record.phrase = new_text
    db.session.commit()
    return None


def remove_phrase_from_list(list_record: ListRecord, phrase_id: int) -> bool:
    link = ListPhrase.query.filter_by(list_id=list_record.id, phrase_id=phrase_id).first()
    if not link:
        return False
    db.session.delete(link)
    db.session.commit()
    return True


def export_phrases_to_text(list_record: ListRecord | None) -> str:
    phrases = get_phrases_sorted(list_record)
    return "\n".join(p.phrase for p in phrases)
