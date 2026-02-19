from datetime import datetime
from enum import Enum
from typing import List

from extensions import db


class ExtremistStatus(str, Enum):
    FIZ = "fiz"
    UR = "ur"


class ExtremistArea(str, Enum):
    INTERNATIONAL = "international"
    RUSSIAN = "russian"


class ExtremistTerrorist(db.Model):
    __tablename__ = "extremists_terrorists"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.Text, nullable=True)
    search_terms = db.Column(db.JSON, nullable=True)
    status = db.Column(db.String(20), nullable=False)
    area = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @classmethod
    def get_by_term(cls, term: str) -> List["ExtremistTerrorist"]:
        rows = cls.query.filter(cls.search_terms.isnot(None)).all()
        return [r for r in rows if term in (r.search_terms or [])]
