"""Create settings_profile table

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "settings_profile",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "is_default", sa.Boolean(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes
    op.create_index("idx_profile_name", "settings_profile", ["name"], unique=True)
    op.create_index(
        "idx_profile_is_default", "settings_profile", ["is_default"], unique=False
    )
    op.create_index(
        "idx_profile_updated_at", "settings_profile", ["updated_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("idx_profile_updated_at", table_name="settings_profile")
    op.drop_index("idx_profile_is_default", table_name="settings_profile")
    op.drop_index("idx_profile_name", table_name="settings_profile")
    op.drop_table("settings_profile")
