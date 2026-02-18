from datetime import datetime
from enum import Enum
from typing import List

from extensions import db


class AgentType(str, Enum):
    FIZ = "fiz"
    UR = "ur"
    OTHER = "other"
    ILLEGAL_PUBLIC_ASSOCIATIONS = "illegal_public_associations"
    FOREIGN_ILLEGAL_ORGANIZATIONS = "foreign_illegal_organizations"


AGENT_TYPE_SHORT_LABELS: dict[str, str] = {
    AgentType.FIZ.value: "ФЛ",
    AgentType.UR.value: "ЮЛ",
    AgentType.OTHER.value: "Иное",
    AgentType.ILLEGAL_PUBLIC_ASSOCIATIONS.value: "ООД без ЮЛ",
    AgentType.FOREIGN_ILLEGAL_ORGANIZATIONS.value: "Иностр. структуры",
}

AGENT_TYPE_MAP: dict[str, str] = {
    AgentType.FIZ.value: "физические лица",
    AgentType.UR.value: "юридические лица",
    AgentType.OTHER.value: "иные объединения лиц",
    AgentType.ILLEGAL_PUBLIC_ASSOCIATIONS.value: "общественные объединения, действующие без образования юридического лица",
    AgentType.FOREIGN_ILLEGAL_ORGANIZATIONS.value: "иностранные структуры без образования юридического лица",
}

class Inagent(db.Model):
    __tablename__ = "inagents"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    moderated = db.Column(db.Boolean, default=False, nullable=False)
    registry_number = db.Column(db.Integer, nullable=True)
    full_name = db.Column(db.Text, nullable=True)
    include_reason = db.Column(db.Text, nullable=True)
    agent_type = db.Column(db.String(100), nullable=True)
    reg_num = db.Column(db.String(100), nullable=True)
    inn = db.Column(db.String(100), nullable=True)
    ogrn = db.Column(db.String(100), nullable=True)
    snils = db.Column(db.String(100), nullable=True)
    participants = db.Column(db.Text, nullable=True)
    address = db.Column(db.Text, nullable=True)
    domain_name = db.Column(db.JSON, nullable=True)
    special_account_num = db.Column(db.String(100), nullable=True)
    bank_name_location = db.Column(db.Text, nullable=True)
    bank_bik = db.Column(db.String(100), nullable=True)
    bank_corr_account = db.Column(db.Text, nullable=True)
    birth_date = db.Column(db.Date, nullable=True)
    include_minjust_date = db.Column(db.Date, nullable=True)
    exclude_minjust_date = db.Column(db.Date, nullable=True)
    publish_date = db.Column(db.Date, nullable=True)
    account_open_date = db.Column(db.Date, nullable=True)
    contract_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    search_terms = db.Column(db.JSON, nullable=True)

    @classmethod
    def get_by_term(cls, term: str) -> List["Inagent"]:
        """Return inagents whose search_terms list contains the given term."""
        rows = cls.query.filter(cls.search_terms.isnot(None)).all()
        return [r for r in rows if term in (r.search_terms or [])]
