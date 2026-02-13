"""inagents table

Revision ID: 4e5f_inagents
Revises: 3c4d_lists_phrases
Create Date: 2026-02-10

"""
from alembic import op
import sqlalchemy as sa


revision = "4e5f_inagents"
down_revision = "3c4d_lists_phrases"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inagents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("moderated", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("registry_number", sa.Integer(), nullable=True),
        sa.Column("full_name", sa.Text(), nullable=True),
        sa.Column("include_reason", sa.Text(), nullable=True),
        sa.Column("agent_type", sa.String(100), nullable=True),
        sa.Column("reg_num", sa.String(100), nullable=True),
        sa.Column("inn", sa.String(100), nullable=True),
        sa.Column("ogrn", sa.String(100), nullable=True),
        sa.Column("snils", sa.String(100), nullable=True),
        sa.Column("participants", sa.Text(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("domain_name", sa.JSON(), nullable=True),
        sa.Column("special_account_num", sa.String(100), nullable=True),
        sa.Column("bank_name_location", sa.Text(), nullable=True),
        sa.Column("bank_bik", sa.String(100), nullable=True),
        sa.Column("bank_corr_account", sa.Text(), nullable=True),
        sa.Column("search_terms", sa.JSON(), nullable=False, default=[]),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("include_minjust_date", sa.Date(), nullable=True),
        sa.Column("exclude_minjust_date", sa.Date(), nullable=True),
        sa.Column("publish_date", sa.Date(), nullable=True),
        sa.Column("account_open_date", sa.Date(), nullable=True),
        sa.Column("contract_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("inagents")
