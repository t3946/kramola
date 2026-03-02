from datetime import datetime
from enum import Enum
from typing import List

from extensions import db


class ExtremistStatus(str, Enum):
    FIZ = "fiz"
    UR = "ur"


EXTREMIST_TYPE_LABELS: dict[str, str] = {
    ExtremistStatus.FIZ.value: "ФЛ",
    ExtremistStatus.UR.value: "ЮЛ",
}

class ExtremistArea(str, Enum):
    INTERNATIONAL = "international"
    RUSSIAN = "russian"


EXTREMIST_AREA_LABELS: dict[str, str] = {
    ExtremistArea.INTERNATIONAL.value: "Международный",
    ExtremistArea.RUSSIAN.value: "Российский",
}


class ExtremistTerrorist(db.Model):
    __tablename__ = "extremists_terrorists"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    raw_source = db.Column(db.Text, nullable=True)
    full_name = db.Column(db.Text, nullable=True)
    search_terms = db.Column(db.JSON, nullable=True)
    type = db.Column(db.String(20), nullable=False)
    area = db.Column(db.String(20), nullable=False)
    sanction_code = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    birth_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @classmethod
    def get_by_term(cls, term: str) -> List["ExtremistTerrorist"]:
        rows = cls.query.filter(cls.search_terms.isnot(None)).all()
        return [r for r in rows if term in (r.search_terms or [])]
