"""add user_message_logs table

Revision ID: 52ad3736198c
Revises: 20b33b55b1fd
Create Date: 2025-09-23 10:21:40.651084

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "52ad3736198c"
down_revision: Union[str, Sequence[str], None] = "20b33b55b1fd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "HD_USER_MESSAGE_LOGS",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("message", sa.String(), nullable=True),
        sa.Column("llm_answer", sa.String(), nullable=True),
        sa.Column("class_name", sa.String(), nullable=True),
        sa.Column("confidence", sa.String(), nullable=True),
        sa.Column("date_of_creation", sa.DateTime(timezone=True), nullable=True),
        sa.Column("date_of_update", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("HD_USER_MESSAGE_LOGS")
