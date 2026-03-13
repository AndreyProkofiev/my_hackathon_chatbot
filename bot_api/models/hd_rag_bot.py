from datetime import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from bot_api.database import Base


def get_current_time():
    return datetime.now().replace(microsecond=0)


class HdRagBotLogs(Base):
    __tablename__ = "HD_RAG_BOT_LOGS"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    user_id = Column(String, nullable=True)
    user_pid = Column(String, nullable=True)
    theme_code = Column(String, nullable=True)
    question = Column(String, nullable=True)
    answer = Column(String, nullable=True)
    response_id = Column(String, nullable=True)
    date_of_creation = Column(DateTime(timezone=True), default=get_current_time)
    date_of_update = Column(DateTime(timezone=True), nullable=True)
