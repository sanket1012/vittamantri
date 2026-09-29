"""add member_invites table

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-29

"""
import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "member_invites",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("household_id", sa.BigInteger(), sa.ForeignKey("households.id"), nullable=False),
        sa.Column("phone_number", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("token", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("created_by", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("accepted_user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('pending','accepted','cancelled')", name="ck_member_invites_status"),
        sa.UniqueConstraint("token", name="uq_member_invites_token"),
    )
    op.create_index("ix_member_invites_household_id", "member_invites", ["household_id"])


def downgrade() -> None:
    op.drop_index("ix_member_invites_household_id", table_name="member_invites")
    op.drop_table("member_invites")
