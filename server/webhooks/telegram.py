import asyncio
import random

import ujson
from pymystem3 import Mystem
from sanic import response
from sanic.views import HTTPMethodView

from clients.telegram import tgclient
from core.cache import cache
from core.db import db
from settings import settings
from utils.dicts import DictUtils
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils

RISK_WORDS = [
    ['суицид'], ['самоубийства'], ['жизненный', 'ситуация'], ['плохой', 'аппетит']
]

m = Mystem()

HOME_BUTTON = [{
    'text': '🏠 Вернуться в меню',
}]

MENU_BUTTONS = [
    [{
        'text': 'ℹ️ О боте',
    }],
    [{
        'text': '📃️ Справка',
    }],
    [{
        'text': '🎼 Генерация музыки',
    }],
]


class TelegramWebhookHandler(HTTPMethodView):
    @classmethod
    async def generate_questions(cls, customer_id, _type):
        items = await db.fetch(
            '''
            SELECT c.id, count(*) AS count_questions, array_agg(q.id) AS question_ids, c.attempt
            FROM public.questions q
            LEFT JOIN public.categories c on c.id = q.category_id
            WHERE c.type = $1
            GROUP BY c.id
            ''',
            _type
        )
        question_ids = []
        for item in items:
            if item.get('count_questions') > item.get('attempt'):
                question_ids.extend(random.sample(item['question_ids'], item.get('attempt')) or [])
            else:
                question_ids.extend(item['question_ids'])

        questions = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT *
            FROM public.questions
            WHERE id = ANY($1)
            ORDER BY position
            ''',
            question_ids
        )) or []

        await cache.setex(f'art:telegram:questions:{customer_id}', 600, ujson.dumps(questions))

        return questions

    @classmethod
    async def finalize(cls, customer_id):
        await cache.delete(f'art:telegram:questions:{customer_id}')
        await cache.delete(f'art:question:name:{customer_id}')
        await cache.delete(f'art:telegram:prev_question:{customer_id}')
        await cache.delete(f'art:telegram:words:{customer_id}')
        await cache.delete(f'art:telegram:audio:name{customer_id}')
        await cache.delete(f'art:telegram:audio:{customer_id}')

    @classmethod
    async def generate_turn(cls, customer_id, chat_id):
        words = await cache.lrange(f'art:telegram:words:{customer_id}', 0, -1)
        if words:
            tune = await db.fetchrow(
                '''
                SELECT *
                FROM public.tunes
                ORDER BY (
                    SELECT COUNT(*)
                    FROM unnest(words) AS element1
                    INNER JOIN unnest($1::text[]) AS element2 ON element1 = element2
                ) DESC
                LIMIT 1;
                ''',
                list(set(words))
            )

            await tgclient.api_call(
                method_name='sendMessage',
                payload={
                    'chat_id': chat_id,
                    'text': '⏱️ идет генерация трека ...'
                }
            )

            await asyncio.sleep(5)

            if tune:
                await cache.setex(f'art:telegram:audio:{customer_id}', 600, tune['id'])
                await tgclient.api_call(
                    method_name='sendAudio',
                    payload={
                        'chat_id': chat_id,
                        'title': tune['title'],
                        'audio': settings['base_url'] + '/static/uploads/' + tune['path'],
                        'reply_markup': {
                            'keyboard': [
                                            [{'text': '\u2069Сохранить трек'}]
                                        ] + [HOME_BUTTON],
                            'one_time_keyboard': True,
                            'resize_keyboard': True
                        }
                    }
                )
            else:
                await tgclient.api_call(
                    method_name='sendMessage',
                    payload={
                        'chat_id': chat_id,
                        'text': 'Ничего не найдено',
                        'reply_markup': {
                            'keyboard': MENU_BUTTONS,
                            'one_time_keyboard': True,
                            'resize_keyboard': True
                        }

                    }
                )

        else:
            await tgclient.api_call(
                method_name='sendMessage',
                payload={
                    'chat_id': chat_id,
                    'text': 'Выберите',
                    'reply_markup': {
                        'keyboard': [
                                        [{'text': '🛠️ Выбор параметров'}]
                                    ] + [HOME_BUTTON],
                        'one_time_keyboard': True,
                        'resize_keyboard': True
                    }

                }
            )

        return

    async def get(self, request):
        return response.json({})

    async def post(self, request):
        data = request.json

        print(f'[post] data: {data}')

        message = DictUtils.as_dict(data.get('message'))
        callback_query = DictUtils.as_dict(data.get('callback_query'))

        if message:
            chat_id = StrUtils.to_str(message.get('chat', {}).get('id'))
            sender = message.get('from', {})
            customer = await db.fetchrow(
                '''
                SELECT id, username
                FROM public.customers
                WHERE uid = $1
                ''',
                chat_id
            )
        elif callback_query:
            chat_id = StrUtils.to_str(callback_query.get('message', {}).get('chat', {}).get('id'))
            sender = callback_query.get('from', {})
            customer = await db.fetchrow(
                '''
                SELECT id, username
                FROM public.customers
                WHERE uid = $1
                ''',
                chat_id
            )
        else:
            return response.json({})

        if not customer:
            customer = await db.fetchrow(
                '''
                INSERT INTO public.customers(name, username, uid)
                VALUES ($1, $2, $3)
                ON CONFLICT DO NOTHING
                RETURNING id, username
                ''',
                sender.get('first_name'),
                sender.get('username'),
                chat_id
            )

        if message and message.get('text') == '/start':
            await self.finalize(customer['id'])
            await tgclient.api_call(
                method_name='sendPhoto',
                payload={
                    'chat_id': chat_id,
                    'caption': '*Что умеет этот бот?*\n\n'
                               'Подбор музыки, соответствующей текущему эмоциональному состоянию пользователя '
                               'Генерация мелодии на основе заданного настроения и предпочтений пользователя',
                    'photo': 'https://art.ttshop.kz/static/uploads/d9/54/d95401ed-cfee-4970-b1e4-91b9ec380ab1.png',
                    'parse_mode': 'Markdown',
                    'reply_markup': {
                        'keyboard': MENU_BUTTONS,
                        'one_time_keyboard': True,
                        'resize_keyboard': True
                    }
                }
            )

            await tgclient.api_call(
                method_name='sendMessage',
                payload={
                    'chat_id': chat_id,
                    'text': 'Привет! Меня зовут TulparIfy. '
                            'Я здесь, чтобы помочь тебе с помощью арт-терапии через музыку.'
                            'Как тебя зовут?',
                    'reply_markup': {
                        'keyboard': [HOME_BUTTON],
                        'one_time_keyboard': True,
                        'resize_keyboard': True
                    }
                }
            )
            await cache.setex(f'art:question:name:{customer["id"]}', 600, '1')

            return response.json({})

        text = None
        success = False
        questions = None
        if message and message.get('text'):
            text = message['text']

        if callback_query and callback_query.get('data'):
            text = callback_query['data']

        if text and text.startswith('🏠'):
            await self.finalize(customer['id'])
            await tgclient.api_call(
                payload={
                    'chat_id': chat_id,
                    'text': 'Выберите',
                    'reply_markup': {
                        'keyboard': MENU_BUTTONS,
                        'one_time_keyboard': True,
                        'resize_keyboard': True
                    }
                }
            )

            return response.json({})

        elif text and text.startswith('🎼'):
            await tgclient.api_call(
                payload={
                    'chat_id': chat_id,
                    'text': 'Выберите',
                    'reply_markup': {
                        'keyboard': [
                                        [{'text': '🛠️ Выбор параметров'}],
                                        [{'text': '🔎 Генерация трека'}]
                                    ] + [HOME_BUTTON],
                        'one_time_keyboard': True,
                        'resize_keyboard': True
                    }
                }
            )

            return response.json({})

        elif text and text.startswith('🛠'):
            await self.finalize(customer['id'])
            questions = await self.generate_questions(customer['id'], 'ai')

        elif text and text.startswith('\u2069'):
            await cache.setex(f'art:telegram:audio:name{customer["id"]}', 600, '1')
            await tgclient.api_call(
                method_name='sendMessage',
                payload={
                    'chat_id': chat_id,
                    'text': 'Название',
                    'reply_markup': {
                        'keyboard': [HOME_BUTTON],
                        'one_time_keyboard': True,
                        'resize_keyboard': True
                    }
                }
            )
            return response.json({})

        elif await cache.get(f'art:telegram:audio:name{customer["id"]}'):
            turn_id = IntUtils.to_int(await cache.get(f'art:telegram:audio:{customer["id"]}'))
            name = await cache.get(f'art:telegram:audio:name{customer["id"]}')
            if not name:
                await tgclient.api_call(
                    method_name='sendMessage',
                    payload={
                        'chat_id': chat_id,
                        'text': 'Название',
                        'reply_markup': {
                            'keyboard': [HOME_BUTTON],
                            'one_time_keyboard': True,
                            'resize_keyboard': True
                        }
                    }
                )
                await cache.setex(f'art:telegram:audio:name{customer["id"]}', 600, '1')

                return response.json({})

            if turn_id:
                t = 'Сохранено'
                await db.fetchrow(
                    '''
                    INSERT INTO public.playlist(turn_id, type, customer_id, title)
                    VALUES ($1, $2, $3, $4)
                    RETURNING *
                    ''',
                    turn_id,
                    'save',
                    customer['id'],
                    text
                )
            else:
                t = 'Ничего не найден'

            await tgclient.api_call(
                method_name='sendMessage',
                payload={
                    'chat_id': chat_id,
                    'text': t,
                    'reply_markup': {
                        'keyboard': [HOME_BUTTON],
                        'one_time_keyboard': True,
                        'resize_keyboard': True
                    }
                }
            )

            await cache.delete(f'art:telegram:audio:name{customer["id"]}')
            await cache.delete(f'art:telegram:audio:{customer["id"]}')

            return response.json({})

        elif text and text.startswith('🔎'):
            await self.generate_turn(customer['id'], chat_id)
            await self.finalize(customer['id'])

            return response.json({})

        if await cache.get(f'art:question:name:{customer["id"]}'):
            await cache.delete(f'art:question:name:{customer["id"]}')

            await db.execute(
                '''
                UPDATE public.customers
                SET name = $2
                WHERE id = $1
                ''',
                customer['id'],
                text
            )

            await tgclient.api_call(
                method_name='sendMessage',
                payload={
                    'chat_id': chat_id,
                    'text': 'Выберите',
                    'reply_markup': {
                        'keyboard': MENU_BUTTONS,
                        'one_time_keyboard': True,
                        'resize_keyboard': True
                    }
                }
            )

            return response.json({})

        if not questions:
            questions = await cache.get(f'art:telegram:questions:{customer["id"]}')
            if questions:
                questions = ujson.loads(questions)

        if text:
            success, method = True, 'sendMessage'
            while success:
                prev_question = await cache.get(f'art:telegram:prev_question:{customer["id"]}')

                if questions:
                    pass
                elif not prev_question:
                    success = False
                    continue

                question, genre = None, None
                if prev_question:
                    prev_question = ujson.loads(prev_question)
                    if prev_question['buttons']:
                        question = prev_question
                        for x in prev_question['buttons']:
                            if text == x['text']:
                                question = None
                                genre = x['callback_data']

                    lemmas = m.lemmatize(text)
                    risk_words = RISK_WORDS + (prev_question.get('details') or {}).get('risk_words', [])

                    flag = True
                    for x in risk_words:
                        if len(list(set(x) & set(lemmas))) == len(x):
                            await tgclient.api_call(
                                payload={
                                    'chat_id': chat_id,
                                    'text': 'Рекомендую обратиться к профессиональному психологу или психотерапевту,'
                                            ' если это беспокоит длительное время. Арт-терапия может быть эффективным '
                                            'дополнением к другим методам лечения депрессии, таким как медикаментозная '
                                            'терапия и психотерапия',
                                    'reply_markup': {
                                        'keyboard': [HOME_BUTTON],
                                        'one_time_keyboard': True,
                                        'resize_keyboard': True
                                    }
                                }
                            )

                            await self.finalize(customer['id'])
                            flag = False

                    if flag is False:
                        break

                if not question:
                    question = questions.pop(0) if questions else {}

                payload, end = {'chat_id': chat_id}, False

                if question:
                    if genre:
                        await cache.lpush(f'art:telegram:words:{customer["id"]}', genre)

                    if question.get('media'):
                        payload['audio'] = question['media']['url']
                        payload['caption'] = question['text']
                        method = 'sendAudio'

                    else:
                        payload['text'] = question['text']

                    await cache.setex(f'art:telegram:prev_question:{customer["id"]}', 600, ujson.dumps(question))
                    await cache.setex(f'art:telegram:questions:{customer["id"]}', 600, ujson.dumps(questions))

                else:
                    end = True
                    payload['text'] = 'Выберите'

                if end:
                    payload.update({
                        'reply_markup': {
                            'keyboard': [
                                            [{'text': '🔎 Генерировать трек'}]
                                        ] + [HOME_BUTTON],
                            'one_time_keyboard': True,
                            'resize_keyboard': True
                        }
                    })
                elif question and question['buttons']:
                    payload.update({
                        'reply_markup': {
                            'keyboard': [
                                [{
                                    'text': button['text'],
                                }] for button in question['buttons'] + HOME_BUTTON
                            ],
                            'one_time_keyboard': True,
                            'resize_keyboard': True
                        }
                    })
                else:
                    payload.update({
                        'reply_markup': {
                            'keyboard': [
                                HOME_BUTTON
                            ],
                            'one_time_keyboard': True,
                            'resize_keyboard': True
                        }
                    })

                await tgclient.api_call(method_name=method, payload=payload)
                break

        if success is False:
            if text and text.startswith('📃️'):
                buttons = await db.fetchval(
                    '''
                    SELECT array_agg(title)
                    FROM public.kbase
                    WHERE type = 'reference'
                    '''
                )
                await tgclient.api_call(
                    payload={
                        'chat_id': chat_id,
                        'text': 'Выберите',
                        'reply_markup': {
                            'keyboard': [
                                            [{'text': x}] for x in buttons
                                        ] + [HOME_BUTTON],
                            'one_time_keyboard': True,
                            'resize_keyboard': True
                        }
                    }
                )

                return response.json({})

            elif text and text.startswith('ℹ️'):
                await tgclient.api_call(
                    method_name='sendPhoto',
                    payload={
                        'chat_id': chat_id,
                        'caption': '*Что умеет этот бот?*\n\n'
                                   'Подбор музыки, соответствующей текущему эмоциональному состоянию пользователя '
                                   'Генерация мелодии на основе заданного настроения и предпочтений пользователя',
                        'photo': 'https://art.ttshop.kz/static/uploads/d9/54/d95401ed-cfee-4970-b1e4-91b9ec380ab1.png',
                        'parse_mode': 'Markdown',
                        'reply_markup': {
                            'keyboard': MENU_BUTTONS,
                            'one_time_keyboard': True,
                            'resize_keyboard': True
                        }
                    }
                )

                return response.json({})

            elif text and text.startswith('🎧'):
                await tgclient.api_call(
                    payload={
                        'chat_id': chat_id,
                        'text': 'Выберите',
                        'reply_markup': {
                            'keyboard': [
                                            [{'text': '🔍 Поиск музыки'}],
                                            [{'text': '🔥 Популярное'}],
                                            [{'text': '✨ Новинки'}],
                                        ] + [HOME_BUTTON],
                            'one_time_keyboard': True,
                            'resize_keyboard': True
                        }
                    }
                )

                return response.json({})

            kbase = await db.fetchrow(
                '''
                SELECT *
                FROM public.kbase
                WHERE title = $1
                ''',
                text
            )
            if kbase:
                await tgclient.api_call(
                    payload={
                        'chat_id': chat_id,
                        'text': kbase['response'],
                        'reply_markup': {
                            'keyboard': MENU_BUTTONS,
                            'one_time_keyboard': True,
                            'resize_keyboard': True
                        }
                    }
                )

            else:
                await tgclient.api_call(
                    payload={
                        'chat_id': chat_id,
                        'text': 'В системе ничего не найдено',
                        'reply_markup': {
                            'keyboard': MENU_BUTTONS,
                            'one_time_keyboard': True,
                            'resize_keyboard': True
                        }
                    }
                )

        return response.json({})
