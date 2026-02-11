from datetime import datetime

from extensions import db

AGENT_TYPE_MAP = {
    "fiz": "физические лица",
    "ur": "юридические лица",
    "other": "иные объединения лиц",
    "illegal_public_associations": "общественные объединения, действующие без образования юридического лица",
    "foreign_illegal_organizations": "иностранные структуры без образования юридического лица",
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
