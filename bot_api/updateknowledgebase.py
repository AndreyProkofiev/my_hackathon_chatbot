#updateknowledgebase.py
import os
import pandas as pd
from atlassian import Confluence
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document
from yandex_chain import YandexLLM, YandexGPTModel
from yandex_chain import YandexEmbeddings
from langchain_chroma import Chroma
from bot_api.settings import settings

import os
import pandas as pd
from yandex_chain import YandexLLM
from langchain.text_splitter import RecursiveCharacterTextSplitter


def mk_page_id_int(page_id):
    """Преобразует ID страницы в int."""
    return int(page_id)

def get_page_text_content(confluence, page_id):
    """Получает чистый текст страницы Confluence."""
    try:
        response = confluence.get_page_by_id(page_id, expand='body.storage')
        content = response['body']['storage']['value']
        soup = BeautifulSoup(content, 'html.parser')
        return soup.get_text(separator=' ', strip=True)
    except Exception as e:
        print(f"Ошибка при извлечении текста со страницы {page_id}: {e}")
        return ""

def get_file_links_from_page(confluence, page_id):
    """
    Возвращает словарь: {имя_файла: ссылка_на_скачивание}
    """
    file_dict = {}
    try:
        attachments = confluence.get_attachments_from_content(page_id=page_id, expand='version')
        base_url = confluence.url.rstrip('/')
        for att in attachments.get('results', []):
            filename = att['title']
            download_url = f"{base_url}{att['_links']['download']}"
            file_dict[filename] = download_url
    except Exception as e:
        print(f"Ошибка при получении файлов со страницы {page_id}: {e}")
    return file_dict

def estimate_tokens(text):
    """
    Оценка количества токенов в тексте (приблизительно).
    """
    words = len(text.split())
    return int(words * 1.3)

def get_confluence_pages_with_content_and_files(confluence, root_page_id, base_url='https://wiki.renins.com'):
    """
    Рекурсивно собирает все дочерние страницы Confluence.
    Возвращает DataFrame с текстом, метаданными и файлами в формате dict.
    """
    root_page_id = mk_page_id_int(root_page_id)
    base_url = base_url.strip().rstrip('/')
    
    data = []
    visited_ids = set()
    queue = [root_page_id]

    print(f"Начинаем обход с корневой страницы: {root_page_id}")

    while queue:
        page_id = queue.pop(0)
        if page_id in visited_ids:
            continue

        print(f"Обработка страницы: {page_id}")

        try:
            page_info = confluence.get_page_by_id(page_id)
            title = page_info['title']
            link = f"{base_url}/pages/viewpage.action?pageId={page_id}"
        except Exception as e:
            print(f"Ошибка при получении базовой информации для страницы {page_id}: {e}")
            title = "Unknown"
            link = f"{base_url}/pages/viewpage.action?pageId={page_id}"

        # Получаем даты через history
        try:
            history = confluence.history(page_id)
            created_date = history.get("createdDate", "N/A")
            last_updated = history.get("lastUpdated", {}).get("when", "N/A")
        except Exception as e:
            print(f"Ошибка при получении истории для страницы {page_id}: {e}")
            created_date = "N/A"
            last_updated = "N/A"

        # Получаем текст
        text_content = get_page_text_content(confluence, page_id)

        # Подсчёт метрик
        text_length = len(text_content)
        word_count = len(text_content.split())
        token_count = estimate_tokens(text_content)

        # Получаем файлы в виде словаря {filename: url}
        file_dict = get_file_links_from_page(confluence, page_id)

        # Добавляем в список
        data.append({
            'id': page_id,
            'title': title,
            'link': link,
            'createdDate': created_date,
            'lastUpdated': last_updated,
            'text': text_content,
            'text_length': text_length,
            'word_count': word_count,
            'token_count': token_count,
            'files': file_dict  # Теперь это dict, а не строка
        })

        # Добавляем дочерние страницы в очередь
        try:
            children = confluence.get_child_pages(page_id)
            for child in children:
                child_id = mk_page_id_int(child['id'])
                if child_id not in visited_ids and child_id not in queue:
                    queue.append(child_id)
        except Exception as e:
            print(f"Ошибка при получении дочерних страниц для {page_id}: {e}")

        visited_ids.add(page_id)

    # Создаём DataFrame
    df = pd.DataFrame(data)
    df.drop_duplicates(subset=['id'], keep='first', inplace=True)

    # Переупорядочиваем колонки
    columns = [
        'id', 'title', 'link', 'createdDate', 'lastUpdated',
        'text', 'text_length', 'word_count', 'token_count', 'files'
    ]
    df = df[columns]

    print(f"✅ Обработка завершена. Найдено {len(df)} страниц.")
    return df



def split_text_into_chunks(text: str, token_count: int, max_tokens_per_chunk: int = 500) -> List[str]:
    """
    Разбивает текст на чанки по приблизительному количеству токенов.
    Использует простое разделение по предложениям и словам.
    Предполагается, что 1 слово ≈ 1.3 токена (грубая эвристика для русского языка).
    Можно заменить на tiktoken, если модель и токенизатор известны.
    """
    if token_count <= max_tokens_per_chunk:
        return [text]
    
    words = text.split()
    chunks = []
    current_chunk = []
    current_token_count = 0
    
    # Грубая оценка: 1 слово ≈ 1.3 токена
    tokens_per_word = 1.3
    
    for word in words:
        word_token_est = len(word) / 5  # альтернативная грубая оценка длины слова
        word_token_est = max(word_token_est, 1)
        
        if current_token_count + word_token_est > max_tokens_per_chunk:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_token_count = word_token_est
            else:
                current_chunk = [word]
                current_token_count = word_token_est
        else:
            current_chunk.append(word)
            current_token_count += word_token_est
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    # Фолбэк: если всё же слишком длинный чанк (редко), можно обрезать
    # Но лучше использовать нормальный токенизатор
    return chunks

def mk_short(x):
    return x[0:100]

# === Основной код преобразования DataFrame ===
def mk_chunked_data(df):
    max_tokens_per_chunk = 500
    chunked_data = []
    df['tittext'] = df['title'] +' '+df['text']

    for idx, row in df.iterrows():
        text = row['tittext']
        token_count = row['token_count']
        page_id = row['id']
        title = row['title']
        link = row['link']
        
        # Разбиваем только если текст длинный
        if pd.isna(text) or not text.strip() or token_count == 0:
            continue  # пропускаем пустые
        
        if token_count <= max_tokens_per_chunk:
            chunked_data.append({
                'id': page_id,
                'title': title,
                'link': link,
                'text_chunk': text,
                'chunk_token_count': token_count,
                'chunk_index': 0
            })
        else:
            chunks = split_text_into_chunks(text, token_count, max_tokens_per_chunk)
            for i, chunk in enumerate(chunks):
                chunk_token_count = len(chunk.split()) * 1.3  # грубая оценка
                chunked_data.append({
                    'id': page_id,
                    'title': title,
                    'link': link,
                    'text_chunk': chunk,
                    'chunk_token_count': int(chunk_token_count),
                    'chunk_index': i
                })

    # Создаём новый DataFrame
    df_chunks = pd.DataFrame(chunked_data)

    # Опционально: сортируем
    df_chunks = df_chunks.sort_values(by=['id', 'chunk_index']).reset_index(drop=True)

    return df_chunks



#gen_hypothetical_questions.py


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100
)

def generate_questions_from_text(text: str, num_questions_per_chunk: int = 2) -> list:
    """
    Генерирует список вопросов на основе текста.
    """
    llm = YandexLLM(
    folder_id=settings.YANDEX_FOLDER_ID, 
    api_key=settings.YANDEX_API_KEY)

    if not text or len(text.strip()) == 0:
        return []

    # Делим на чанки
    chunks = text_splitter.split_text(text)
    all_questions = []

    for chunk in chunks:
        prompt = f"""
        Ниже приведён фрагмент инструкции. 
        Сгенерируй {num_questions_per_chunk} наиболее вероятных вопроса, 
        который мог бы задать пользователь, читающий этот текст.

        Вопросы должны быть краткими, понятными и соответствовать стилю поддержки.

        Текст:
        {chunk}

        Верни только вопросы, каждый с новой строки, без нумерации и пояснений.
        """

        try:
            response = llm(prompt.strip())
            questions = [q.strip() for q in response.strip().split('\n') if q.strip()]
            all_questions.extend(questions)
        except Exception as e:
            print(f"❌ Ошибка при генерации вопросов: {e}")
            continue

    return list(set(all_questions))  # убираем дубли

def generate_questions_for_dataframe(df: pd.DataFrame, text_column='text', output_column='generated_questions') -> pd.DataFrame:
    """
    Применяет генерацию вопросов ко всему DataFrame.
    """
    print(f"Начинаем генерацию вопросов для {len(df)} инструкций...")

    df_copy = df.copy()
    df_copy[output_column] = None
    df_copy[output_column] = df_copy[output_column].astype('object')

    for idx, row in df_copy.iterrows():
        print(f"Обработка: {row['title']} (ID: {row['id']})")
        questions = generate_questions_from_text(row[text_column])
        df_copy.at[idx, output_column] = questions

    return df_copy



def generate_qa_pairs_for_text(text: str, num_pairs: int = 3) -> list:
    """
    Генерирует список пар "вопрос-ответ" на основе текста инструкции.
    Возвращает список словарей: [{"question": "...", "answer": "..."}, ...]
    """
    if not text or len(text.strip()) == 0:
        return []
    
    llm = YandexLLM(
        folder_id=settings.YANDEX_FOLDER_ID,
        api_key=settings.YANDEX_API_KEY
    )

    prompt = f"""
    Ниже приведена инструкция. 
    Сгенерируй ровно {num_pairs} пары "вопрос-ответ", основанные на этом тексте.

    Требования:
    - Вопросы должны быть реалистичными, как если бы их задал пользователь.
    - Ответы должны быть краткими, точными и взятыми из текста.
    - Не выдумывай информацию, которой нет в инструкции.
    - Формат: каждый блок в виде:
        Вопрос: ...
        Ответ: ...

    Инструкция:
    {text[:7000]}  # Ограничиваем длину, чтобы не превысить контекст

    Сгенерируй ровно {num_pairs} пары:
    """

    try:
        response = llm(prompt.strip())
    except Exception as e:
        print(f"❌ Ошибка при вызове YandexGPT: {e}")
        return []

    # Парсим ответ: ищем строки "Вопрос: ..." и "Ответ: ..."
    import re
    qa_list = []
    question_pattern = r"Вопрос:\s*(.+?)(?=\nОтвет:|\Z)"
    answer_pattern = r"Ответ:\s*(.+?)(?=\nВопрос:|\Z)"

    questions = re.findall(question_pattern, response, re.DOTALL)
    answers = re.findall(answer_pattern, response, re.DOTALL)

    # Обрезаем по num_pairs
    for q, a in list(zip(questions, answers))[:num_pairs]:
        qa_list.append({
            "question": q.strip(),
            "answer": a.strip()
        })

    # Если не удалось распарсить, но ответ есть — возвращаем как есть (резерв)
    if len(qa_list) == 0:
        qa_list.append({
            "question": "Какие действия описаны в этой инструкции?",
            "answer": "Не удалось сгенерировать пары. Ответ временный."
        })

    return qa_list

def add_qa_pairs_to_dataframe(df: pd.DataFrame, text_column='text', output_column='qa_pairs') -> pd.DataFrame:
    """
    Добавляет в DataFrame столбец с парами вопрос-ответ.
    """
    print(f"🚀 Начинаем генерацию пар 'вопрос-ответ' для {len(df)} инструкций...")

    df_copy = df.copy()
    df_copy[output_column] = None
    df_copy[output_column] = df_copy[output_column].astype('object')  # чтобы можно было класть списки

    for idx, row in df_copy.iterrows():
        text = row[text_column]
        if not text or len(text.strip()) == 0:
            print(f"⚠️ Пропуск: пустой текст — {row['title']} (ID: {row['id']})")
            continue

        print(f"📝 Обработка: {row['title']} (ID: {row['id']})")
        qa_pairs = generate_qa_pairs_for_text(text, num_pairs=3)
        df_copy.at[idx, output_column] = qa_pairs

    # print("✅ Генерация завершена.")
    return df_copy


def update_chroma_db(
    new_df: pd.DataFrame,
    persist_directory: str = "./chroma_confluence_kb_qa",
    embeddings = None  # передай HuggingFaceEmbeddings() или YandexEmbeddings()
):
    """
    Обновляет Chroma DB, добавляя новые и обновлённые страницы по полю 'id'.
    
    :param new_df: DataFrame с колонками: id, title, link, text_chunk, chunk_index, qa_pairs (list of dicts)
    :param persist_directory: путь к Chroma DB
    :param embeddings: объект эмбеддингов (HuggingFaceEmbeddings, YandexEmbeddings и т.п.)
    """
    if embeddings is None:
        raise ValueError("embeddings must be provided")

    # Подключаемся к существующей базе
    db = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )

    # Получаем все существующие документы (или хотя бы их метаданные)
    # Вместо загрузки всех документов — можно использовать фильтрацию
    collection = db.get()

    # Создаём словарь: id -> list[doc_id] в Chroma
    doc_ids_to_delete = []

    # Множество ID из нового датасета
    new_page_ids = set(new_df['id'].astype(str))

    # Проходим по всем документам в Chroma
    for i, metadata in enumerate(collection['metadatas']):
        page_id = str(metadata.get("id"))
        if page_id in new_page_ids:
            doc_id = collection['ids'][i]
            doc_ids_to_delete.append(doc_id)

    # Удаляем старые версии страниц
    if doc_ids_to_delete:
        db.delete(ids=doc_ids_to_delete)
        print(f"Удалено {len(doc_ids_to_delete)} чанков для обновления {len(new_page_ids)} страниц")

    # --- Теперь добавляем новые/обновлённые данные ---
    documents = []
    metadatas = []
    ids = []
    chunk_id_counter = 0

    for _, row in new_df.iterrows():
        page_id = str(row['id'])
        title = row['title']
        link = row['link']
        text_chunk = row['text_chunk']
        chunk_index = int(row['chunk_index'])

        # Уникальный ID для чанка
        chunk_id = f"chunk_{page_id}_{chunk_index}_{chunk_id_counter}"
        chunk_id_counter += 1

        documents.append(text_chunk)
        metadatas.append({
            "source_type": "chunk",
            "id": page_id,
            "title": title,
            "link": link,
            "chunk_index": chunk_index,
            "qa_pair": ""  # пусто для чанков
        })
        ids.append(chunk_id)

        # Добавляем QA-пары, если есть
        qa_list = row.get('qa_pairs', []) or []
        for q_idx, qa in enumerate(qa_list):
            if not isinstance(qa, dict):
                continue
            question = qa.get('question', '').strip()
            answer = qa.get('answer', '').strip()
            if not question:
                continue

            qa_id = f"qa_{page_id}_{chunk_index}_{q_idx}_{chunk_id_counter}"
            chunk_id_counter += 1

            documents.append(question)
            metadatas.append({
                "source_type": "question",
                "id": page_id,
                "title": title,
                "link": link,
                "chunk_index": chunk_index,
                "qa_pair_question": question,
                "qa_pair_answer": answer
            })
            ids.append(qa_id)

    # Добавляем в Chroma
    if documents:
        db.add_texts(texts=documents, metadatas=metadatas, ids=ids)
        print(f"Добавлено {len(documents)} новых/обновлённых чанков и QA-пар")
    else:
        print("Нет данных для добавления")

    # Сохраняем изменения (если нужно)
    db.persist()
    return {
        "status": "success",
        "processed_pages": len(new_page_ids),
        "details": [{"page_id": pid, "action": "updated"} for pid in new_page_ids]
    }
