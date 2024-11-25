from langchain_chroma import Chroma
from yandex_chain import YandexEmbeddings
import langchain.chains
import langchain.prompts
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from yandex_chain import YandexGPTClassifier

auth = {
    "folder_id" : os.environ['folder_id'].strip(), 
    "api_key" : os.environ['api_key'].strip()
}


class Agent:
    
    def __call__(self, state):
        # do something
        return "new_namestate"
    



class NaiveRAG(Agent):

    prompt = """
Пожалуйста, посмотри на текст ниже и ответь на вопрос, используя информацию из этого текста. Выведи только
краткий ответ, не надо пояснительного текста.
Текст:
-----
{context}
-----
Вопрос:
{question}"""

    def join_docs(self,docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def __init__(self,num_documents=5):
        self.embeddings = YandexEmbeddings(**auth)
        self.db = Chroma(embedding_function=self.embeddings, persist_directory='../simple_rag/chroma_db')
        self.llm = YandexLLM(model=YandexGPTModel.Pro,**auth)
        self.template = langchain.prompts.PromptTemplate(
            template=self.prompt, input_variables=["context", "question"])
        self.retriever = self.db.as_retriever(
            search_type="mmr", search_kwargs={"k": num_documents})
        self.chain = (
            {"context": self.retriever | self.join_docs, "question": RunnablePassthrough()}
            | self.template
            | self.llm
            | StrOutputParser()
        )

    def __call__(self, state):
        state['output'] = self.chain.invoke(state['input'])
        return 'конец'
    



class NER(Agent):
    def __init__(self, prompt, on_success, on_fail, labels=None):
        self.llm = YandexLLM(model=YandexGPTModel.Pro, **auth)
        self.prompt = prompt
        self.labels = labels
        self.lowlabels = [ x.lower() for x in labels ] if labels else None
        self.on_success = on_success
        self.on_fail = on_fail

    def __call__(self, state):
        res = self.llm.invoke(self.prompt.replace('{}',state['input']))
        if res=="NONE" or res=='(NONE)':
            return self.on_fail
        if '('in res: res = res[res.index('(')+1:]
        if ')' in res: res = res[:res.index(')')]
        res = [x.strip() for x in res.split('|')]
        if self.labels:
            res = [ x for x in res if x.lower() in self.lowlabels ]
        res = [x for x in res if x!="NONE"]
        if len(res)==0:
            return self.on_fail
        state['entities'] = res
        return self.on_success
    

class AgentRuntime:
    def __init__(self,states):
        self.states = states
        
    def run(self, state, start_state, verbose=False):
        s = start_state
        while True:
            if verbose:
                print(f"Executing state: {s}, state = {state}")
            A = self.states[s]
            s = A(state)
            if s == 'конец' or s is None:
                break
        return state



class Classfier(Agent):
    def __init__(self, task_description, labels, samples=None):
        self.classifier = YandexGPTClassifier(task_description, labels, samples, **auth)

    def __call__(self, state):
        res = self.classifier.invoke(state['input'])
        c = self.classifier.get_top_label(res)
        return c
    
InputClassifier = Classfier(
    """Определи, содержится ли в вопросе одна из следующих задач:
* подобрать вино к еде (подбор_вина),
* подобрать еду к вину (подбор_еды),
* другой вопрос (другая_тема)""",
    ["подбор_вина","подбор_еды","другая_тема"]
)

for s in sentences:
    res = InputClassifier(mkstate(s))
    print(f"{s} -> {res}")