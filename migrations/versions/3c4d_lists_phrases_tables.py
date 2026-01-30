"""lists phrases tables

Revision ID: 3c4d_lists_phrases
Revises: 2b1c_user_single_role
Create Date: 2026-01-29

"""
from sqlalchemy import inspect

from alembic import op
import sqlalchemy as sa


revision = "3c4d_lists_phrases"
down_revision = "2b1c_user_single_role"
branch_labels = None
depends_on = None


def _existing_tables(connection) -> set[str]:
    return set(inspect(connection).get_table_names())


def upgrade():
    conn = op.get_bind()
    existing = _existing_tables(conn)

    if "pl_lists" not in existing:
        op.create_table(
            "pl_lists",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("slug", sa.String(length=100), nullable=False),
            sa.Column("title", sa.String(length=100), nullable=False),
            sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
            sa.UniqueConstraint("slug"),
        )
    if "pl_phrases" not in existing:
        op.create_table(
            "pl_phrases",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("phrase", sa.Text(), nullable=False),
            sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
    if "pl_phrases_lists" not in existing:
        op.create_table(
            "pl_phrases_lists",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("list_id", sa.Integer(), nullable=False),
            sa.Column("phrase_id", sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("phrase_id", "list_id", name="unique_phrase_list"),
        )
        op.create_foreign_key(
            "fk_pl_phrases_lists_phrase",
            "pl_phrases_lists",
            "pl_phrases",
            ["phrase_id"],
            ["id"],
            ondelete="CASCADE",
        )
        op.create_foreign_key(
            "fk_pl_phrases_lists_list",
            "pl_phrases_lists",
            "pl_lists",
            ["list_id"],
            ["id"],
            ondelete="CASCADE",
        )
    if "pl_lists_logs" not in existing:
        op.create_table(
            "pl_lists_logs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column("list_id", sa.Integer(), nullable=False),
            sa.Column("phrase", sa.Text(), nullable=False),
            sa.Column("add_date", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.Column("remove_date", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_foreign_key(
            "fk_pl_lists_logs_list",
            "pl_lists_logs",
            "pl_lists",
            ["list_id"],
            ["id"],
            ondelete="CASCADE",
        )

def downgrade():
    op.drop_table("pl_lists_logs")
    op.drop_table("pl_phrases_lists")
    op.drop_table("pl_phrases")
    op.drop_table("pl_lists")
