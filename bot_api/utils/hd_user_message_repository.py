from uuid import UUID

from sqlalchemy.orm import Session

from bot_api.models.hd_user_message import HdUserMessageLogs


class HdUserMessageLogsRepository:
    def __init__(self, session: Session):
        self._session = session

    def create(self, fields: dict):
        db_record = HdUserMessageLogs(**fields)
        self._session.add(db_record)
        self._session.commit()
        self._session.refresh(db_record)

    def update(self, identifier: UUID, fields: dict):
        self._session.query(HdUserMessageLogs).filter(
            HdUserMessageLogs.id == identifier
        ).update(fields)
        self._session.commit()
