"""add telegram link token columns to users

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-28

"""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("telegram_link_token", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("telegram_link_token_expires_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.create_unique_constraint("uq_users_telegram_link_token", "users", ["telegram_link_token"])


def downgrade() -> None:
    op.drop_constraint("uq_users_telegram_link_token", "users", type_="unique")
    op.drop_column("users", "telegram_link_token_expires_at")
    op.drop_column("users", "telegram_link_token")
