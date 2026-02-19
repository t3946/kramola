"""pl_lists color column

Revision ID: 5a6b_pl_lists_color
Revises: 4e5f_inagents
Create Date: 2026-02-19

"""
from alembic import op
import sqlalchemy as sa


revision = "5a6b_pl_lists_color"
down_revision = "4e5f_inagents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    color_column_def = sa.Column(
        "color",
        sa.String(length=7),
        nullable=False,
        default="#aaaaaa",
    )
    op.add_column("pl_lists", color_column_def)


def downgrade() -> None:
    op.drop_column("pl_lists", "color")
