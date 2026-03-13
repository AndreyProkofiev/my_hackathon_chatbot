from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request

from bot_api.dependencies import get_hd_rag_bot_repository

from bot_api.logger import logger
from bot_api.schemas.hd_rag_bot import (
    ErrorResponse,
    QueryRequest,
    QueryResponse,
)
from bot_api.utils.hd_rag_bot_repository import (
    HdRagBotLogsRepository,
)


router = APIRouter(tags=["База Знаний"])


@router.post(
    "/ask",
    response_model=QueryResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
    },
)
def ask_knowledge_base(
    request: Request,
    data: QueryRequest,
    rag_bot_repo: HdRagBotLogsRepository = Depends(get_hd_rag_bot_repository),
):
    logger.info(f"Поступил запрос - {data.model_dump_json()}")

    response_id = str(uuid4())
    log_id = uuid4()
    log_data = {
        "id": log_id,
        "theme_code": data.theme_code,
        "user_id": data.user_id,
        "user_pid": data.user_pid,
        "question": data.query,
        "response_id": response_id,
    }
    rag_bot_repo.create(fields=log_data)

    logger.info("Передаем данные в ИИ")
    try:
        chain = request.app.state.rag_chain
        answer = chain.invoke(data.query)
        answer = answer.strip()
    except Exception as e:
        logger.info(f"Ошибка при обработке запроса: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при генерации ответа")

    logger.info("Обновляем запись в БД")
    fields = {
        "answer": answer,
        "date_of_update": datetime.now().replace(microsecond=0),
    }
    rag_bot_repo.update(identifier=log_id, fields=fields)

    logger.info("Возвращаем ответ пользователю")
    return QueryResponse(
        response_id=response_id,
        message=answer,
        links=[],
        theme_code=data.theme_code,
        user_id=data.user_id,
        user_pid=data.user_pid,
    )
