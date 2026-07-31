"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-31

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import CITEXT, UUID

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")

    op.create_table(
        "households",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("household_id", sa.BigInteger(), sa.ForeignKey("households.id"), nullable=False),
        sa.Column("username", CITEXT(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("role IN ('admin','member')", name="ck_users_role"),
        sa.UniqueConstraint("username", name="uq_users_username"),
        sa.UniqueConstraint("telegram_id", name="uq_users_telegram_id"),
    )

    op.create_table(
        "transactions",
        sa.Column("id", UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("household_id", sa.BigInteger(), sa.ForeignKey("households.id"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("time", sa.Time(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("subcategory", sa.Text(), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("source", sa.Text(), nullable=False, server_default=""),
        sa.Column("logged_by", sa.Text(), nullable=False, server_default="Unknown"),
        sa.Column("logged_by_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("input_method", sa.Text(), nullable=False, server_default="text"),
        sa.Column("raw_input", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
        sa.CheckConstraint("type IN ('income','expense')", name="ck_transactions_type"),
    )
    op.create_index("ix_txn_household_date", "transactions", ["household_id", sa.text("date DESC")])
    op.create_index("ix_txn_household_user", "transactions", ["household_id", "logged_by_id"])
    op.create_index("ix_txn_household_cat", "transactions", ["household_id", "category"])

    op.create_table(
        "custom_categories",
        sa.Column("household_id", sa.BigInteger(), sa.ForeignKey("households.id"), primary_key=True),
        sa.Column("name", sa.Text(), primary_key=True),
        sa.Column("emoji", sa.Text(), nullable=False, server_default="🏷️"),
    )
    op.create_table(
        "custom_subcategories",
        sa.Column("household_id", sa.BigInteger(), sa.ForeignKey("households.id"), primary_key=True),
        sa.Column("category_name", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), primary_key=True),
    )
    op.create_table(
        "deleted_categories",
        sa.Column("household_id", sa.BigInteger(), sa.ForeignKey("households.id"), primary_key=True),
        sa.Column("name", sa.Text(), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("deleted_categories")
    op.drop_table("custom_subcategories")
    op.drop_table("custom_categories")
    op.drop_index("ix_txn_household_cat", table_name="transactions")
    op.drop_index("ix_txn_household_user", table_name="transactions")
    op.drop_index("ix_txn_household_date", table_name="transactions")
    op.drop_table("transactions")
    op.drop_table("users")
    op.drop_table("households")
