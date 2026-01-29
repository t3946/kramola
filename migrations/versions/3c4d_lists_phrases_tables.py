"""lists phrases tables

Revision ID: 3c4d_lists_phrases
Revises: 2b1c_user_single_role
Create Date: 2026-01-29

"""
from alembic import op
import sqlalchemy as sa


revision = "3c4d_lists_phrases"
down_revision = "2b1c_user_single_role"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "pl_lists",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "pl_phrases",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("phrase", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phrase"),
    )
    op.create_table(
        "pl_phrases_lists",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("list_id", sa.Integer(), nullable=False),
        sa.Column("phrase_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["phrase_id"], ["pl_phrases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["list_id"], ["pl_lists.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phrase_id", "list_id", name="unique_phrase_list"),
    )
    op.create_table(
        "pl_lists_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("list_id", sa.Integer(), nullable=False),  # Добавлен list_id как колонка
        sa.Column("phrase", sa.String(length=200), nullable=False),
        sa.Column("add_date", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("remove_date", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["list_id"], ["pl_lists.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

def downgrade():
    op.drop_table("pl_lists_logs")
    op.drop_table("pl_phrases_lists")
    op.drop_table("pl_phrases")
    op.drop_table("pl_lists")
