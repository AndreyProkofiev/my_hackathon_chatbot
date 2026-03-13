from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, Request

from bot_api.bot.llm_chain import ask_user
from bot_api.bot.classifier import mk_classyfi
from bot_api.dependencies import get_hd_user_message_repository
from bot_api.logger import logger
from bot_api.schemas.hd_rag_bot import (
    ErrorResponse,
    UserMessageResponse,
    UserMessageRequest,
)
from bot_api.utils.hd_user_message_repository import (
    HdUserMessageLogsRepository,
)


router = APIRouter(tags=["База Знаний"])


@router.post(
    "/user_mess",
    response_model=UserMessageResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
    },
)
async def process_user_message(
    request: Request,
    data: UserMessageRequest,
    user_message_repo: HdUserMessageLogsRepository = Depends(
        get_hd_user_message_repository
    ),
):
    logger.info(f"Поступил запрос - {data.model_dump_json()}")
    log_id = uuid4()
    log_data = {
        "id": log_id,
        "message": data.message,
    }
    user_message_repo.create(fields=log_data)

    logger.info("Передаем данные в ИИ")
    classyfi_answ = mk_classyfi(data.message)
    class_name, confidence = classyfi_answ[0], classyfi_answ[1]

    if class_name == "консультация" and confidence > 0.55:
        answer = request.app.state.rag_chain.invoke(data.message).strip()
        class_ = class_name
    elif confidence > 0.55:
        answer = ""
        class_ = class_name
    else:
        answer = ask_user()
        class_ = "прочее"

    logger.info("Обновляем запись в БД")
    fields = {
        "llm_answer": answer,
        "class_name": class_,
        "confidence": str(confidence),
        "date_of_update": datetime.now().replace(microsecond=0),
    }
    user_message_repo.update(identifier=log_id, fields=fields)

    logger.info("Возвращаем ответ пользователю")
    return UserMessageResponse(LLM_answ=answer, class_=class_)
