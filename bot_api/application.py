import pandas as pd
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List
from contextlib import asynccontextmanager
from yandex_chain import YandexEmbeddings
from atlassian import Confluence
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from bot_api.bot.llm_chain import create_rag_chain
from bot_api.endpoints import list_of_routes
from bot_api.logger import logger
from bot_api.settings import settings


from bot_api.schemas.hd_rag_bot import UpdateMessageRequest, UpdateMessageResponse
from bot_api.updateknowledgebase import (
    update_chroma_db,  
    add_qa_pairs_to_dataframe, 
    get_confluence_pages_with_content_and_files, 
    mk_chunked_data 
    )

from atlassian import Confluence
# Управление жизненным циклом
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Загружаем RAG-цепочку...")
    try:
        app.state.rag_chain = create_rag_chain()
        logger.info("RAG chain загружена")
    except Exception as e:
        logger.info(f"Ошибка при загрузке модели: {e}")
        raise e

    yield
    logger.info("Сервис остановлен")


def get_app() -> FastAPI:
    def bind_routes(fastapi_application: FastAPI, application_settings) -> None:
        for route in list_of_routes:
            fastapi_application.include_router(
                route, prefix=application_settings.PATH_PREFIX
            )

    tags_metadata = [
        {
            "name": "База Знаний",
            "description": "Методы для работы с Базой Знаний",
        },
        {
            "name": "Тест",
            "description": "Проверка работоспособности сервиса",
        },
    ]
    application = FastAPI(
        title="RAG Bot API HD",
        description="API HD Bot",
        docs_url="/swagger",
        openapi_url="/openapi.json",
        version="1.0.0",
        openapi_tags=tags_metadata,
        lifespan=lifespan,
    )
    bind_routes(application, settings)
    application.state.settings = settings
    return application


app = get_app()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"status": "400 Bad Request", "message": "Invalid request format"},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


executor = ThreadPoolExecutor(max_workers=2)

@app.post("/mk_update", response_model=UpdateMessageResponse)
async def process_update_knwdb(data: UpdateMessageRequest):
    """
    Принимает список page_ids и запускает фоновое обновление базы знаний.
    Возвращает 200 сразу.
    """
    if not data.page_ids:
        return UpdateMessageResponse(
            status="empty_request",
            processed_pages=0,
            details=[{"message": "No page IDs provided"}]
        )

    # Запускаем обновление в фоне
    asyncio.create_task(
        run_update_in_background(data.page_ids)
    )

    # Сразу возвращаем успешный ответ
    return UpdateMessageResponse(
        status="accepted",
        processed_pages=len(data.page_ids),
        details=[{"message": "Update task started in background"}]
    )


async def run_update_in_background(page_ids: List[str]):
    """Выполняет обновление Chroma в фоновом потоке."""
    loop = asyncio.get_event_loop()
    try:
        # Запускаем синхронную функцию в ThreadPool
        await loop.run_in_executor(executor, _sync_update_knowledge_base, page_ids)
    except Exception as e:
        # Логируем ошибку (в продакшене — через logger)
        print(f"❌ Ошибка в фоновом обновлении: {e}")
        # Можно отправить алерт, записать в БД и т.д.


def _sync_update_knowledge_base(page_ids: List[str]):
    """Синхронная функция обновления — вся тяжёлая логика здесь."""
    try:
        confluence = Confluence(
            url='https://wiki.renins.com',  # УБРАЛ ЛИШНИЕ ПРОБЕЛЫ!
            username=settings.CONFLUENCE_USER,
            password=settings.CONFLUENCE_PASSWORD
        )
        embeddings = YandexEmbeddings(
            folder_id=settings.YANDEX_FOLDER_ID,
            api_key=settings.YANDEX_API_KEY
        )

        # Всегда обходим всё дерево от корня (как в вашем коде)
        root_page_id = 168267644
        full_df = get_confluence_pages_with_content_and_files(confluence, root_page_id)

        if full_df.empty:
            print("⚠️ Нет данных для обновления")
            return

        df_chunks = mk_chunked_data(full_df)
        df_with_qa = add_qa_pairs_to_dataframe(
            df_chunks, 
            text_column='text_chunk', 
            output_column='qa_pairs'
        )
        result = update_chroma_db(
            df_with_qa, 
            "/usr/src/app/bot_api/bot/chroma_confluence_kb_09092025", 
            embeddings
        )
        print(f"✅ Обновление завершено: {result}")
    except Exception as e:
        print(f"❌ Критическая ошибка в _sync_update_knowledge_base: {e}")
        raise

# @app.post("/mk_update", response_model=UpdateMessageResponse)
# async def process_update_knwdb(data: UpdateMessageRequest):
#     # Используем переданные ID или дефолтный
#     # page_ids = data.page_ids if data.page_ids else ["168267644"]
#     # page_ids = eval(data.page_ids)

#     confluence = Confluence(
#         url='https://wiki.renins.com/',
#         username=settings.CONFLUENCE_USER,
#         password=settings.CONFLUENCE_PASSWORD
#     )
#     embeddings = YandexEmbeddings(
#         folder_id=settings.YANDEX_FOLDER_ID,
#         api_key=settings.YANDEX_API_KEY
#     )

#     # all_dfs = []
#     # for pid in page_ids:
#     #     # pid_int = int(pid)
#     #     df = get_confluence_pages_with_content_and_files(confluence, pid)
#     #     if not df.empty:
#     #         all_dfs.append(df)

#     # if not all_dfs:
#     #     return UpdateMessageResponse(
#     #         status="no_content",
#     #         processed_pages=0,
#     #         details=[{"error": "No pages found"}]
#     #     )
#     if len(data.page_ids) >0:
#         root_page_id = 168267644
#         full_df = get_confluence_pages_with_content_and_files(confluence, root_page_id)


#     # full_df = pd.concat(all_dfs, ignore_index=True)
#     df_chunks = mk_chunked_data(full_df)
#     df_with_qa = add_qa_pairs_to_dataframe(df_chunks, text_column='text_chunk', output_column='qa_pairs')
#     result = update_chroma_db(df_with_qa, "/usr/src/app/bot_api/bot/chroma_confluence_kb_09092025", embeddings)
    
#     return UpdateMessageResponse(**result)
