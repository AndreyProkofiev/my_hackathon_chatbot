"""init

Revision ID: 20b33b55b1fd
Revises:
Create Date: 2025-09-22 11:39:15.452262

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20b33b55b1fd"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "HD_RAG_BOT_LOGS",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("user_pid", sa.String(), nullable=True),
        sa.Column("theme_code", sa.String(), nullable=True),
        sa.Column("question", sa.String(), nullable=True),
        sa.Column("answer", sa.String(), nullable=True),
        sa.Column("response_id", sa.String(), nullable=True),
        sa.Column("date_of_creation", sa.DateTime(timezone=True), nullable=True),
        sa.Column("date_of_update", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("HD_RAG_BOT_LOGS")
