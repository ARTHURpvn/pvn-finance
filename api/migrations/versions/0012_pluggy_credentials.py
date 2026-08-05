"""Credenciais Pluggy por usuário (multi-tenant): client_id + client_secret
cifrado + base_url, ligados à conta. Substitui as credenciais do ambiente.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012_pluggy_credentials"
down_revision: str | None = "0011_investment_detail"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pluggy_credentials",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("client_id", sa.String(255), nullable=False),
        sa.Column("encrypted_client_secret", sa.LargeBinary(), nullable=False),
        sa.Column(
            "base_url",
            sa.String(255),
            nullable=False,
            server_default="https://api.pluggy.ai",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "uq_pluggy_credentials_user",
        "pluggy_credentials",
        ["user_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_pluggy_credentials_user", table_name="pluggy_credentials")
    op.drop_table("pluggy_credentials")
