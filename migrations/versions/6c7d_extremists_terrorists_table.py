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
        sa.Column("search_terms", sa.JSON(), nullable=True),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("area", sa.String(20), nullable=False),
        sa.Column("sanction_code", sa.String(255), nullable=True),
        sa.Column("raw_source", sa.Text(), nullable=True),
        sa.Column("birth_place", sa.Text(), nullable=True),
        sa.Column("company_region", sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.execute("CREATE INDEX ix_et_area_sanction_code ON extremists_terrorists (area, sanction_code)")
    op.execute("CREATE INDEX ix_et_area_type ON extremists_terrorists (area, type)")
    op.execute("CREATE INDEX ix_et_area_type_birth ON extremists_terrorists (area, type, birth_date, birth_place(100))")

def downgrade() -> None:
    op.execute("DROP INDEX ix_et_area_sanction_code ON extremists_terrorists")
    op.execute("DROP INDEX ix_et_area_type ON extremists_terrorists")
    op.execute("DROP INDEX ix_et_area_type_birth ON extremists_terrorists")
    op.drop_table("extremists_terrorists")
