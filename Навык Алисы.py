from flask import Flask, request
import logging
import json
import requests


app = Flask(__name__)
logging.basicConfig(level=logging.INFO, filename='app.log',
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')

logging.basicConfig(level=logging.DEBUG)


def log():
    logging.debug('Debug')
    logging.info('Info')
    logging.warning('Warning')
    logging.error('Error')
    logging.critical('Critical or Fatal')

sessionStorage = {}

@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Request: %r', response)
    return json.dumps(response)


sections = ["arts", "automobiles", "books", "business", "fashion",
            "food", "health", "movies", "politics","science",
            "sports", "technology", "theater", "travel"]


def handle_dialog(res, req):
    user_id = req['session']['user_id']

    if req['session']['new']:
        res['response']['text'] = \
            'Привет! Назови свое имя!'
        sessionStorage[user_id] = {
            'first_name': None, 'url':None
        }
        return

    if sessionStorage[user_id]['first_name'] is None:
        # в последнем его сообщение ищем имя.
        first_name = get_first_name(req)
        # если не нашли, то сообщаем пользователю что не расслышали.
        if first_name is None:
            res['response']['text'] = \
                'Не расслышала имя. Повтори, пожалуйста!'
        # если нашли, то приветствуем пользователя.
        # И спрашиваем какой город он хочет увидеть.
        else:
            sessionStorage[user_id]['first_name'] = first_name
            res['response'][
                'text'] = 'Приятно познакомиться, ' + first_name.title() \
                          + '. Я - Алиса. Про что желаешь почитать новости?'
            res['response']['buttons'] = [
                {
                    'title': sections[i],
                    'hide': True
                } for i in range(14)
            ]
            # получаем варианты buttons из ключей нашего словаря cities
    else:
        # Получаем города из нашего город
        section = get_section(req)
        city = get_coordinates(req)
        if section is None:
            res['response']['text'] = 'Ты не ответил на вопрос?'

        elif section in sections:
            res['response']['text'] = "Нажми на кнопку!\nЧтобы прочитать новость."
            index = sections.index(section)
            js = requests.get("https://api.nytimes.com/svc/topstories/v2/"+ section + ".json?api-key=iGSueEfJakK66VXUY0ECerKXZ3lGIXBU").json()
            title = js['results'][0]['title']
            url = js['results'][0]['url']
            sessionStorage[user_id]['url'] = url
            res['response']['buttons'] = [
                    {
                        'title': "Открыть ссылку",
                        'url': url
                    }
                ]
        elif req['request']['original_utterance'] == "Открыть ссылку":
            res['response']['text'] = "Не хотите посмотреть геолокацию данного события?"
            res['response']['buttons'] = [
                    {
                        'title': "Хочу",
                        'hide': True
                    },
                    {
                        'title': "Не хочу",
                        'hide': True
                    }
                ]
        elif req['request']['original_utterance'] == "Хочу":
            res['response']['card'] = {}
            res['response']['card']['type'] = 'BigImage'
            res['response']['card']['title'] = 'Nur-Sultan, Kazakhstan'
            res['response']['card']['image_id'] = "1521359/47096f8c8d90c6c7d59d"
            res['response']['text'] = ' '
            res['response']['buttons'] = [
                    {
                        'title': "Почитать еще новостей",
                        'hide': True
                    },
                    {
                        'title': "Завершить работу",
                        'hide': True
                    }
                ]
        elif req['request']['original_utterance'] == "Почитать еще новостей":
            res['response']['text'] = "Выберите категорию"
            res['response']['buttons'] = [
            {
                'title': sections[i],
                'hide': True
            } for i in range(14)
            ]
        else:
            res['response']['text'] = "Хорошего дня!\nСпасибо за использование навыка Алисы!"
            res['end_session'] = True





def get_section(req):
    est = False
    section = " "
    for j in range(14):
        if sections[j] in req['request']['original_utterance']:
            est = True
            section = sections[j]
    return section

def get_coordinates(req):
    try:
        section = get_section(req)
        js = requests.get("https://api.nytimes.com/svc/topstories/v2/"+ section + ".json?api-key=iGSueEfJakK66VXUY0ECerKXZ3lGIXBU").json()
        # получаем JSON ответа
        # получаем координаты города (там написаны долгота(longitude),
        # широта(latitude) через пробел).
        # Посмотреть подробное описание JSON-ответа можно
        # в документации по адресу
        # https://tech.yandex.ru/maps/geocoder/
        coordinates_str = js['results'][0]['geo_facet']
        # Превращаем string в список, так как точка -
        # это пара двух чисел - координат
        long, lat = map(float, coordinates_str.split())
        # Вернем ответ
        return long, lat
    except Exception as e:
        return e

def get_image(req, ll, spn):
    res = requests.get("https://static-maps.yandex.ru/1.x/?" + long + "," + lat + "&spn=0.016457,0.00619&l=map")

    return res

def image(url):
    img = requests.get(url)
    f = {'file': img.content}
    return request.post('https://dialogs.yandex.net/api/v1/skills/443fbd7b-d880-4de9-871a-810a740e87eb/images', files=f,
                        headers={'Authorization': 'OAuth AQAAAAAgQEMJAAT7o1ZMa7CzxUDzt4G2NF-GyJA', 'Content - Type': 'multipart/ form - data'}).json()['image']['id']

def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name',
            # то возвращаем ее значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    app.run()