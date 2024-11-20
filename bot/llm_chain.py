import os

import langchain.chains
import langchain.prompts
from yandex_chain import YandexEmbeddings
from yandex_chain import YandexLLM, YandexGPTModel
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


embeddings = YandexEmbeddings(
    folder_id=os.environ['folder_id'], 
    api_key=os.environ['api_key'])

db = Chroma(embedding_function=embeddings, persist_directory='./chroma_db')

retriever = db.as_retriever(search_type="mmr", search_kwargs={"k": 5})


llm = YandexLLM(folder_id=os.environ['folder_id'],
                api_key=os.environ['api_key'],
                model=YandexGPTModel.Pro)


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

def join_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# Создаём цепочку
chain = (
    {"context": retriever | join_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)
