"""Create the End-user and OAuth account tables."""

import uuid

import sqlalchemy as sa
from alembic import op
from fastapi_users_db_sqlalchemy.generics import GUID

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def _uuid(name: str, *extra: sa.ForeignKey) -> sa.Column[uuid.UUID]:
    return sa.Column(name, GUID(), *extra, primary_key=not extra, nullable=False)


def upgrade() -> None:
    _ = op.create_table(
        "user",
        _uuid("id"),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=1024), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
    )
    _ = op.create_index("ix_user_email", "user", ["email"], unique=True)
    _ = op.create_table(
        "oauth_account",
        _uuid("id"),
        _uuid("user_id", sa.ForeignKey("user.id", ondelete="CASCADE")),
        sa.Column("oauth_name", sa.String(length=100), nullable=False),
        sa.Column("access_token", sa.String(length=1024), nullable=False),
        sa.Column("expires_at", sa.Integer(), nullable=True),
        sa.Column("refresh_token", sa.String(length=1024), nullable=True),
        sa.Column("account_id", sa.String(length=320), nullable=False),
        sa.Column("account_email", sa.String(length=320), nullable=False),
    )
    _ = op.create_index("ix_oauth_account_account_id", "oauth_account", ["account_id"])
    _ = op.create_index("ix_oauth_account_oauth_name", "oauth_account", ["oauth_name"])


def downgrade() -> None:
    _ = op.drop_index("ix_oauth_account_oauth_name", table_name="oauth_account")
    _ = op.drop_index("ix_oauth_account_account_id", table_name="oauth_account")
    _ = op.drop_table("oauth_account")
    _ = op.drop_index("ix_user_email", table_name="user")
    _ = op.drop_table("user")
