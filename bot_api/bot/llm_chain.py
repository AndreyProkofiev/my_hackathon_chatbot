from collections import Counter

import langchain.chains
import langchain.prompts
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import (
    RunnableParallel,
    RunnablePassthrough,
    RunnableLambda,
)
from yandex_chain import YandexEmbeddings, YandexGPTModel, YandexLLM

from bot_api.settings.default import settings


def create_rag_chain():
    embeddings = YandexEmbeddings(
        folder_id=settings.YANDEX_FOLDER_ID, api_key=settings.YANDEX_API_KEY
    )

    db = Chroma(
        embedding_function=embeddings,
        persist_directory="/usr/src/app/bot_api/bot/chroma_confluence_kb_09092025",
    )

    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 5})

    llm = YandexLLM(
        temperature=0,
        folder_id=settings.YANDEX_FOLDER_ID,
        api_key=settings.YANDEX_API_KEY,
        model=YandexGPTModel.Pro,
    )

    prompt = """
        Пожалуйста, посмотри на текст ниже и ответь на вопрос, используя информацию из этого текста. Выведи только
        краткий ответ, не надо пояснительного текста.
        Текст:
        -----
        {context}
        -----
        Вопрос:
        {question}"""

    prompt = langchain.prompts.PromptTemplate(
        template=prompt, input_variables=["context", "question"]
    )

    def prepare_context_and_links(docs):

        context = "\n\n".join(doc.page_content for doc in docs)

        links = [doc.metadata["link"] for doc in docs]

        link_counts = Counter(links)

        most_common_link = link_counts.most_common(1)[0][0]  # всегда будет хотя бы одна

        return {"context": context, "selected_link": most_common_link}

    generation_chain = prompt | llm | StrOutputParser()

    chain = (
        RunnableParallel(
            {
                "data": retriever | prepare_context_and_links,
                "question": RunnablePassthrough(),
            }
        )
        | RunnableLambda(
            lambda x: {
                "answer": generation_chain.invoke(
                    {"context": x["data"]["context"], "question": x["question"]}
                ),
                "link": x["data"]["selected_link"],
            }
        )
        | RunnableLambda(
            lambda x: x["answer"]
            + f"\n\nБолее подробно смотри на странице: {x['link']}"
        )
    )
    return chain


llm = YandexLLM(
    temperature=0,
    folder_id=settings.YANDEX_FOLDER_ID,
    api_key=settings.YANDEX_API_KEY,
    model=YandexGPTModel.Pro,
)


def ask_user(
    to_user="перефразируй вежливо фразу : Если ты напишешь больше деталей, мне будет проще понять вопрос и помочь тебе.",
):
    return llm.invoke(to_user)
