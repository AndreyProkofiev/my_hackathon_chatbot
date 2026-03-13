from datetime import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from bot_api.database import Base


def get_current_time():
    return datetime.now().replace(microsecond=0)


class HdUserMessageLogs(Base):
    __tablename__ = "HD_USER_MESSAGE_LOGS"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    message = Column(String, nullable=True)
    llm_answer = Column(String, nullable=True)
    class_name = Column(String, nullable=True)
    confidence = Column(String, nullable=True)
    date_of_creation = Column(DateTime(timezone=True), default=get_current_time)
    date_of_update = Column(DateTime(timezone=True), nullable=True)
