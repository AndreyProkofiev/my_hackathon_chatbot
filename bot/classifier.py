import os
import sys
import numpy as np
from langchain_chroma import Chroma
from yandex_chain import YandexEmbeddings
import langchain.chains
import langchain.prompts
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from yandex_chain import YandexGPTClassifier
from dotenv import load_dotenv

load_dotenv('ya.env')

auth = {
    "folder_id" : os.environ['folder_id'].strip(), 
    "api_key" : os.environ['api_key'].strip()
}


def get_class(cl_resp):
    conf = []
    for cl in cl_resp:
        conf.append(cl['confidence'])
    res = cl_resp[conf.index(max(conf))]['label']
    return res


descr = "Пожалуйста, определи, является ли предложение просьбой скинут пароль, перезагрузить, получить консультацию"
classes = ["пароль", "перезагрузка", "консультация"]


samp_j = [ {
        "label": "пароль",
        "text": "Прошу восстановить пароль в компьютер (Вайс) сотрудника Sandreev"
    },
    {
        "label": "пароль",
        "text": "При вводе пароля появляется сообщение об ошибке\n\nВозможно временный пароль жил 3 дня, а перед праздниками заболел и не\nзашел, а теперь надо пароль заново задать?"
    },
    {
        "label": "пароль",
        "text": "Прошу разблокировать учетную запись сотрудника"
    },
    {
        "label": "пароль",
        "text": "Не могу войти на удаленку, видимо надо было пароль поменять, не успела . Проверьте пожалуйста "
    },
    {
        "label": "пароль",
        "text": "не могу войти в компьютер"
    },
    {
        "label": "перезагрузка",
        "text": "не могу войти в компьютер"
    },
    {
        "label": "перезагрузка",
        "text": "Включить удаленный комп. Имя ПК WS-CZC108B6CR"
    },
    {
        "label": "перезагрузка",
        "text": "Не получается подключиться к удаленному рабочему столу\nКомп: WS-CZC108B6CR, логин TGdvjbkdcbd"
    },
    {
        "label": "перезагрузка",
        "text": "Недоступна машина ws-sybase02. Находится в одной из серверных.\n\nПрошу включить/перезагрузить машину WS-CZC108B6CR"
    },
    {
        "label": "перезагрузка",
        "text": "Добрый вечер. Очень виснет удаленный рабочий стол, тормозит, помогите,\nпожалуйста."
    },
    {
        "label": "консультация",
        "text": "Как получить доступ в DataLense?"
    },
    {
        "label": "консультация",
        "text": "Как сменить цветовую палитру в графике DL?"
    },
    {
        "label": "консультация",
        "text": "Как добавить подпись на графике?"
    },
    {
        "label": "консультация",
        "text": "Как создать чарт?"
    },
    {
        "label": "консультация",
        "text": "Как добавить фильтр в дэшборде, связанный с чартами?"
    },
    {
        "label": "консультация",
        "text": "Как предоставить доступ к моему отчету в DL другому пользователю?"
    },
    {
        "label": "консультация",
        "text": "Как подключится к рабочему месту удаленно через Cisсo?"
    },
    {
        "label": "консультация",
        "text": "Как подключится к рабочему месту удаленно через Cisko?"
    },
    {
        "label": "консультация",
        "text": "как зайти в Citrix?"
    },
    {
        "label": "консультация",
        "text": "Как подключится к рабочему месту удаленно через Citrix ?"
    }]


classifier = YandexGPTClassifier(task_description=descr, labels=classes, **auth,samples=samp_j)


def mk_classyfi(q):
    cl_resp = classifier.invoke([q][0])
    return get_class(cl_resp)