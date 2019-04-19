import json
import logging
import random

import requests
from flask import Flask, request

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
coun = False
att = 0
cities = {
    'москва': [
        '213044/0ca73a267e6b5b23073a', '965417/cbe0734f8a72c237ae69'
    ],
    'нью-йорк': [
        '1656841/6466c6d9b591054d7c04', '965417/122d87be6e6db9dd0d15'
    ],
    'париж': [
        '213044/ac52d40231e52484fbcb', '965417/d782de50682bed8f6915'
    ]
}

leng = {'москва': 'ru-ru',
        'нью-йорк': 'ru-en',
        'париж': 'ru-fr'}

flag = {'москва': '1540737/7fb1d000ab6e70bd21b0',
        'нью-йорк': '1540737/fa1cb91461d932867daa',
        'париж': '1652229/cc78b5b43bb3f691ef58'}


def geocoder(geocoder_request):
    response = None
    try:
        response = requests.get(geocoder_request)
        json_response = response.json()
        if response:
            toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
            toponym_okryg = toponym["metaDataProperty"]["GeocoderMetaData"]["Address"]["Components"][0]["name"]
            return toponym_okryg
        else:
            print("Ошибка выполнения запроса:")
            print(geocoder_request)
            print("Http статус:", response.status_code, "(", response.reason, ")")
    except:
        print("Запрос не удалось выполнить. Проверьте наличие сети Интернет.")


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
    logging.info('Response: %r', response)
    return json.dumps(response)


def handle_dialog(res, req):
    global coun
    user_id = req['session']['user_id']
    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови своё имя!'
        sessionStorage[user_id] = {
            'first_name': None,
            'game_started': False
        }
        return

    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
        else:
            sessionStorage[user_id]['first_name'] = first_name
            sessionStorage[user_id]['guessed_cities'] = []
            res['response']['text'] = f'Приятно познакомиться, {first_name.title()}. Я Алиса. Отгадаешь город по фото?'
            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                },
                {
                    "title": "Помощь",
                    "hide": True

                }
            ]

    else:
        if not sessionStorage[user_id]['game_started']:
            if 'да' in req['request']['nlu']['tokens']:
                if len(sessionStorage[user_id]['guessed_cities']) == 3:
                    res['response']['text'] = 'Ты отгадал все города!'
                    res['end_session'] = True
                else:
                    sessionStorage[user_id]['game_started'] = True
                    sessionStorage[user_id]['attempt'] = 1
                    coun = False

                    play_game(res, req)
            elif 'нет' in req['request']['nlu']['tokens']:
                res['response']['text'] = 'Ну и ладно!'
                res['end_session'] = True
            elif 'помощь' in req['request']['nlu']['tokens']:
                res['response']['text'] = 'Это игра - угадай город. Задача игры угадать города по фотографиию.'
            else:
                res['response']['text'] = 'Не поняла ответа! Так да или нет?'

        else:
            play_game(res, req)


def play_game(res, req):
    user_id = req['session']['user_id']
    global coun
    global att
    global leng
    attempt = sessionStorage[user_id]['attempt']

    if attempt == 1:
        city = random.choice(list(cities))
        while city in sessionStorage[user_id]['guessed_cities']:
            city = random.choice(list(cities))
        sessionStorage[user_id]['city'] = city
        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card']['title'] = 'Что это за город?'
        res['response']['card']['image_id'] = cities[city][attempt - 1]
        res['response']['text'] = 'Тогда сыграем!'
    elif coun:
        city = sessionStorage[user_id]['city']

        if geocoder("https://geocode-maps.yandex.ru/1.x/?geocode=" + city + "&format=json").lower() in \
                req['request']['nlu']['tokens']:
            res['response']['text'] = 'Правильно! Сыграем еще?'
            sessionStorage[user_id]['game_started'] = False
            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                },
                {
                    "title": "Помощь",
                    "hide": True

                },
                {
                    "title": "Покажи город на карте",
                    "url": "https://yandex.ru/maps/?mode=search&text=" + city,
                    "hide": True

                }
            ]
        elif geocoder(
                "https://geocode-maps.yandex.ru/1.x/?geocode=" + city + "&format=json").lower() == 'соединённые штаты америки' and (
                (
                        'соединенные штаты америки' in req['request']['nlu']['tokens']) or (
                        'сша' in req['request']['nlu']['tokens'])):
            res['response']['text'] = 'Правильно! Сыграем еще?'
            sessionStorage[user_id]['game_started'] = False
            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                },
                {
                    "title": "Помощь",
                    "hide": True

                },
                {
                    "title": "Покажи город на карте",
                    "url": "https://yandex.ru/maps/?mode=search&text=" + city,
                    "hide": True

                }
            ]
        elif att == 0:
            att += 1
            translator_uri = \
                "https://translate.yandex.net/api/v1.5/tr.json/translate"

            response = requests.get(
                translator_uri,
                params={
                    "key":
                        "trnsl.1.1.20190417T132006Z.32e54f6445ecc603.74d21ce4b9d818e54084e94316c9624049d74d63",
                    "lang": leng[city],
                    "text": 'Привет'
                })

            res['response'][
                'text'] = 'Неправильно. Слово "Привет" на языке на котором говорят в этой стране: ' + "\n\n".join(
                [response.json()["text"][0]])
        elif att == 1:
            att += 1
            res['response']['card'] = {}
            res['response']['card']['type'] = 'BigImage'
            res['response']['card']['title'] = 'Неправильно. Вот тебе флаг этой страны'
            res['response']['card']['image_id'] = flag[city]
            res['response']['text'] = 'А вот и не угадал!'
        else:
            res['response']['text'] = 'Неправильно. Это страна' + geocoder(
                "https://geocode-maps.yandex.ru/1.x/?geocode=" + city + "&format=json")

    else:
        city = sessionStorage[user_id]['city']
        if 'помощь' in req['request']['nlu']['tokens']:
            res['response']['text'] = 'Это игра - угадай город. Задача игры угадать города по фотографиию.'
        elif get_city(req) == city:
            res['response']['text'] = 'Правильно! А в какой стране этот город?'
            sessionStorage[user_id]['guessed_cities'].append(city)
            coun = True
            att = 0

            return
        else:
            # если нет
            if 'помощь' in req['request']['nlu']['tokens']:
                res['response']['text'] = 'Это игра - угадай город. Задача игры угадать города по фотографиию.'
            elif attempt == 3:
                coun = True
                att = 0

                res['response']['text'] = f'Вы пытались. Это {city.title()}. А в какой стране этот город?'
                sessionStorage[user_id]['guessed_cities'].append(city)
                return
            else:
                res['response']['card'] = {}
                res['response']['card']['type'] = 'BigImage'
                res['response']['card']['title'] = 'Неправильно. Вот тебе дополнительное фото'
                res['response']['card']['image_id'] = cities[city][attempt - 1]
                res['response']['text'] = 'А вот и не угадал!'
    sessionStorage[user_id]['attempt'] += 1


def get_city(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            return entity['value'].get('city', None)


def get_first_name(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    app.run()
