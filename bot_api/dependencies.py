from fastapi import Depends

from sqlalchemy.orm import Session

from bot_api.database import get_session
from bot_api.utils.hd_rag_bot_repository import (
    HdRagBotLogsRepository,
)
from bot_api.utils.hd_user_message_repository import (
    HdUserMessageLogsRepository,
)


def get_hd_rag_bot_repository(
    session: Session = Depends(get_session),
) -> HdRagBotLogsRepository:
    return HdRagBotLogsRepository(session=session)


def get_hd_user_message_repository(
    session: Session = Depends(get_session),
) -> HdUserMessageLogsRepository:
    return HdUserMessageLogsRepository(session=session)
