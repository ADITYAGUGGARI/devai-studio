"""Expiring, attempt-limited email authentication challenges."""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "email_challenges",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("address_hash", sa.String(64), nullable=False),
        sa.Column("code_hash", sa.String(64), nullable=False),
        sa.Column("action_hash", sa.String(64), unique=True, nullable=True),
        sa.Column("request_hash", sa.String(64), nullable=True),
        sa.Column("delivery_status", sa.String(20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("consumed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_email_challenges_email", "email_challenges", ["email"])
    op.create_index("ix_email_challenges_address_hash", "email_challenges", ["address_hash"])


def downgrade():
    op.drop_table("email_challenges")
