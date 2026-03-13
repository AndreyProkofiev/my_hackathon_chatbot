import time
from yandex_chain import YandexGPTClassifier

from bot_api.settings.default import settings


auth = {
    "folder_id": settings.YANDEX_FOLDER_ID.strip(),
    "api_key": settings.YANDEX_API_KEY.strip(),
}


def get_class(cl_resp):
    conf = []
    for cl in cl_resp:
        conf.append(cl["confidence"])
    max_cl = cl_resp[conf.index(max(conf))]["label"]
    conf_cl = cl_resp[conf.index(max(conf))]["confidence"]
    return (max_cl, conf_cl)


descr = "Ты классифицируешь обращения в службу технической поддержки страховой компании, определи, является ли предложение просьбой скинут пароль, перезагрузить, получить консультацию, если нет уверенности то к относи к категрии прочее, к консультации относятся любые вопросы связанные с технической поддержкой, нерелевантные вопросы относятся к прочее"

classes = ["пароль", "перезагрузка", "консультация", "прочее"]


samp_j = [
    {
        "label": "пароль",
        "text": "Прошу восстановить пароль в компьютер (Вайс) сотрудника",
    },
    {
        "label": "пароль",
        "text": "При вводе пароля появляется сообщение об ошибке\n\nВозможно временный пароль жил 3 дня, а перед праздниками заболел и не\nзашел, а теперь надо пароль заново задать?",
    },
    {"label": "пароль", "text": "Прошу разблокировать учетную запись сотрудника"},
    {
        "label": "пароль",
        "text": "Не могу войти на удаленку, видимо надо было пароль поменять, не успела . Проверьте пожалуйста ",
    },
    {"label": "пароль", "text": "не могу войти в компьютер"},
    {"label": "перезагрузка", "text": "не могу войти в компьютер"},
    {"label": "перезагрузка", "text": "Включить удаленный комп. Имя ПК"},
    {
        "label": "перезагрузка",
        "text": "Не получается подключиться к удаленному рабочему столу",
    },
    {
        "label": "перезагрузка",
        "text": "Недоступна машина ws-sybase02. Находится в одной из серверных.\n\nПрошу включить/перезагрузить машину",
    },
    {
        "label": "перезагрузка",
        "text": "Добрый вечер. Очень виснет удаленный рабочий стол, тормозит, помогите,\nпожалуйста.",
    },
    {"label": "консультация", "text": "Как настроить, как подключить"},
    {
        "label": "консультация",
        "text": "Как подключится к рабочему месту удаленно через Cisсo или Citrix?",
    },
    {"label": "консультация", "text": "Как подключится к рабочему месту удаленно"},
    {"label": "консультация", "text": "Помогите с проблемой, помогите с вопросом"},
    {"label": "консультация", "text": "Как получить доступ к системе?"},
    {"label": "консультация", "text": "Как оформить"},
    {
        "label": "консультация",
        "text": "По какому адресу обратиться к операционистам по личным видам страхования?",
    },
    {"label": "консультация", "text": "Куда обратиться для расторжения полиса ОСАГО?"},
    {"label": "консультация", "text": "Почему не оформляется полис в В2В?"},
]


classifier = YandexGPTClassifier(
    task_description=descr, labels=classes, **auth, samples=samp_j
)


def mk_classyfi(q: str):
    max_retries = 3
    retry_delay = 2  # секунды

    for attempt in range(max_retries):
        try:
            cl_resp = classifier.invoke(q)
            return get_class(cl_resp)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                # После третьей неудачи возвращаем заглушку
                fallback_response = [
                    {'label': 'пароль', 'confidence': 0.0001},
                    {'label': 'перезагрузка', 'confidence': 0.0001},
                    {'label': 'консультация', 'confidence': 0.0001},
                    {'label': 'прочее', 'confidence': 0.9997}
                ]
                return get_class(fallback_response)
# def mk_classyfi(q: str):
#     cl_resp = classifier.invoke(q)
#     return get_class(cl_resp)
