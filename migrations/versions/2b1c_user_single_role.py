"""user single role

Revision ID: 2b1c_user_single_role
Revises: 1ae146f0744e
Create Date: 2026-01-29

"""
from alembic import op
import sqlalchemy as sa


revision = "2b1c_user_single_role"
down_revision = "1ae146f0744e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("user", sa.Column("role_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_user_role_id",
        "user",
        "role",
        ["role_id"],
        ["id"],
        ondelete="SET NULL",
    )
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE user SET role_id = (SELECT role_id FROM user_roles WHERE user_roles.user_id = user.id LIMIT 1)"
        )
    )
    op.drop_table("user_roles")


def downgrade():
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["role.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "INSERT INTO user_roles (user_id, role_id) SELECT id, role_id FROM user WHERE role_id IS NOT NULL"
        )
    )
    op.drop_constraint("fk_user_role_id", "user", type_="foreignkey")
    op.drop_column("user", "role_id")
