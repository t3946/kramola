"""extremists_terrorists table

Revision ID: 6c7d_extremists_terrorists
Revises: 5a6b_pl_lists_color
Create Date: 2026-02-19

"""
from alembic import op
import sqlalchemy as sa


revision = "6c7d_extremists_terrorists"
down_revision = "5a6b_pl_lists_color"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "extremists_terrorists",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("full_name", sa.Text(), nullable=True),
        sa.Column("search_terms", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("area", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("extremists_terrorists")
